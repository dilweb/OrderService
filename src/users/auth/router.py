from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from src.users.auth.schemas import (
    SUserRegister, 
    UserOut, 
    SUserAuth,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    TokenResponse,
    RefreshTokenRequest
)
from src.users.dao import UserDAO 
from src.db.session import get_session
from src.users.auth.auth import (
    verify_password, 
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_refresh_token,
    verify_refresh_token,
    create_email_verification_token,
    verify_email_verification_token
)
from src.tasks.email_tasks import send_verification_email
from src.settings import settings
from src.users.auth.dependencies import get_user_dao, get_current_user, get_current_admin_user
from src.users.models.user import User
from src.users.auth.dependencies import get_current_admin_user, get_current_super_admin_user


router = APIRouter()


@router.post("/register/")
async def register_user(
    user_data: SUserRegister, 
    user_dao: UserDAO = Depends(get_user_dao)
) -> UserOut:
    user = await user_dao.get_user_by_email(email=user_data.email)
    if user:
        raise HTTPException(409, 'Пользователь уже существует')
    new_user = await user_dao.create_user(user=user_data)
    token = create_email_verification_token(user_id=new_user.id, email=new_user.email)
    verification_link = f"{settings.BASE_URL}/auth/verify-email?token={token}"
    send_verification_email.delay(to_email=new_user.email, verification_link=verification_link)
    return new_user


@router.post("/login/")
async def auth_user(
    response: Response, 
    user_data: SUserAuth, 
    user_dao: UserDAO = Depends(get_user_dao)
) -> TokenResponse:
    user = await user_dao.get_user_by_email(email=user_data.email)
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(401, 'Неверная почта или пароль')
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token(user_id=user.id)
    
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    response.set_cookie(key="users_refresh_token", value=refresh_token, httponly=True)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> UserOut:
    return user_data


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    response.delete_cookie(key="users_refresh_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.post("/refresh/")
async def refresh_tokens(
    http_request: Request,
    response: Response,
    request_body: RefreshTokenRequest | None = None,
    user_dao: UserDAO = Depends(get_user_dao)
) -> TokenResponse:
    """
    Универсальное обновление access и refresh токенов.
    
    Токен можно передать двумя способами:
    1. В теле запроса: {"refresh_token": "..."} - для мобильных/API клиентов
    2. В cookie автоматически - для веб-приложений
    
    Приоритет: сначала проверяется cookie, затем body.
    """
    # Пытаемся получить токен из куки
    refresh_token = http_request.cookies.get('users_refresh_token')
    
    # Если токена нет в куки, пытаемся получить из body
    if not refresh_token:
        refresh_token = request_body.refresh_token if request_body else None
    
    # Если токен не найден ни в body, ни в cookie
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh токен не найден. Передайте токен в body или cookie'
        )
    
    # Проверяем refresh токен
    token_data = verify_refresh_token(token=refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh токен недействителен или истек'
        )
    
    user_id = token_data["user_id"]
    
    # Проверяем, существует ли пользователь
    user = await user_dao.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    # Создаем новую пару токенов
    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user_id=user.id)
    
    # Обновляем cookies
    response.set_cookie(key="users_access_token", value=new_access_token, httponly=True)
    response.set_cookie(key="users_refresh_token", value=new_refresh_token, httponly=True)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.get("/get-user/{id}/")
async def get_user_by_id(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user)
    ) -> UserOut:
    user_dao = UserDAO(session)
    
    user = await user_dao.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    return user


@router.patch("/make-admin/{user_id}/")
async def make_user_admin(
    user_id: int, 
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_super_admin_user)
) -> UserOut:
    user_dao = UserDAO(session)
    
    # Проверяем существование пользователя
    user = await user_dao.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    # Обновляем пользователя (теперь kwargs работают!)
    updated_user = await user_dao.update_user(user_id=user_id, is_admin=True)
    
    return updated_user


@router.get("/users/", dependencies=[Depends(get_current_admin_user)])
async def get_all_users(user_dao: UserDAO = Depends(get_user_dao)) -> List[UserOut]:
    
    users_list = await user_dao.get_users_list()
    if not users_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователи не найдены'
        )
    
    return users_list


@router.post("/password/forgot/")
async def forgot_password(
    request: ForgotPasswordRequest,
    user_dao: UserDAO = Depends(get_user_dao)
):
    """
    Запрос на сброс пароля. 
    Создает JWT токен и отправляет его на email пользователя.
    Токен действителен 1 час.
    """
    user = await user_dao.get_user_by_email(email=request.email)
    if not user:
        # Возвращаем успех даже если пользователь не найден (безопасность)
        return {'message': 'Если email существует, письмо будет отправлено'}
    
    # Создаем JWT токен сброса пароля
    reset_token = create_password_reset_token(user_id=user.id, email=user.email)
    
    # TODO: Отправить email через Celery
    # send_password_reset_email.delay(user.email, reset_token)
    
    # Временно выводим токен в ответе (только для разработки!)
    return {
        'message': 'Письмо с инструкциями отправлено на ваш email',
        'token': reset_token  # Удалить в продакшене!
    }


@router.post("/password/reset/")
async def reset_password(
    request: ResetPasswordRequest,
    user_dao: UserDAO = Depends(get_user_dao)
):
    """
    Сброс пароля по JWT токену из письма.
    Токен содержит user_id и email, проверяется срок действия.
    """
    # Проверяем JWT токен и получаем данные
    token_data = verify_password_reset_token(token=request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Токен недействителен или истек'
        )
    
    user_id = token_data["user_id"]
    email = token_data["email"]
    
    # Получаем пользователя
    user = await user_dao.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    # Дополнительная проверка email для безопасности
    if user.email != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Токен недействителен'
        )
    
    # Меняем пароль
    await user_dao.update_password(user_id=user.id, new_password=request.new_password)
    
    # TODO: Отправить уведомление о смене пароля
    # send_password_changed_notification.delay(user.email)
    
    return {'message': 'Пароль успешно изменен'}


@router.post("/password/change/")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_dao: UserDAO = Depends(get_user_dao)
):
    """
    Смена пароля для авторизованного пользователя.
    Требует указать текущий пароль.
    """
    # Проверяем текущий пароль
    if not verify_password(request.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неверный текущий пароль'
        )
    
    # Проверяем, что новый пароль отличается от старого
    if request.old_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Новый пароль должен отличаться от текущего'
        )
    
    # Меняем пароль
    await user_dao.update_password(user_id=current_user.id, new_password=request.new_password)
    
    # TODO: Отправить уведомление о смене пароля
    # send_password_changed_notification.delay(current_user.email)
    
    return {'message': 'Пароль успешно изменен'}


@router.get("/verify-email")
async def verify_email(
    token: str,
    response: Response,
    user_dao: UserDAO = Depends(get_user_dao),
):
    data = verify_email_verification_token(token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Токен недействителен или истёк'
        )
    await user_dao.user_email_verification(user_id=data["user_id"])
    user_id = data["user_id"]
    access_token = create_access_token({"sub": str(user_id)})
    refresh_token = create_refresh_token(user_id=user_id)
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    response.set_cookie(key="users_refresh_token", value=refresh_token, httponly=True)
    return {"message": "Почта подтверждена"}


@router.delete("/users/delete-my-account/")
async def delete_me(
    current_user: User = Depends(get_current_user),
    user_dao: UserDAO = Depends(get_user_dao),
):
    """
    Удалить свой аккаунт.
    Разрешено: сам пользователь (только свой аккаунт).
    """
    deleted = await user_dao.delete_user(user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return {"message": "Пользователь удалён"}


@router.delete("/users/{user_id}/")
async def delete_user_as_admin(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_dao: UserDAO = Depends(get_user_dao),
):
    """
    Удалить пользователя.
    Разрешено: супер-админ (любой пользователь) или сам пользователь (только свой аккаунт).
    """
    if not current_user.is_super_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Удалять пользователя может только супер-админ или сам пользователь",
        )
    deleted = await user_dao.delete_user(user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    check = await user_dao.get_user_by_id(id=current_user.id)
    if check:
        return {"message": "Пользователь не удалён"}
    return {"message": "Пользователь удалён"}


 