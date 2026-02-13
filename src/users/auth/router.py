from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from src.users.auth.schemas import SUserRegister, UserOut, SUserAuth
from src.users.dao import UserDAO 
from src.db.session import get_session
from src.users.auth.auth import verify_password, create_access_token
from src.users.auth.dependencies import get_user_dao, get_current_user, get_current_admin_user
from src.users.models.user import User


router = APIRouter()


@router.post("/register/")
async def register_user(
    user_data: SUserRegister, 
    user_dao: UserDAO = Depends(get_user_dao)  # ← Проще!
) -> UserOut:
    user = await user_dao.get_user_by_email(email=user_data.email)
    if user:
        raise HTTPException(409, 'Пользователь уже существует')
    new_user = await user_dao.create_user(user=user_data)
    return new_user


@router.post("/login/")
async def auth_user(
    response: Response, 
    user_data: SUserAuth, 
    user_dao: UserDAO = Depends(get_user_dao)
):
    user = await user_dao.get_user_by_email(email=user_data.email)
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(401, 'Неверная почта или пароль')
    
    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return user_data


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/get_user/{id}")
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)) -> UserOut:
    user_dao = UserDAO(session)
    
    user = await user_dao.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    return user


@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def get_all_users(user_dao: UserDAO = Depends(get_user_dao)) -> List[UserOut]:
    
    users_list = await user_dao.get_users_list()
    if not users_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователи не найдены'
        )
    
    return users_list

