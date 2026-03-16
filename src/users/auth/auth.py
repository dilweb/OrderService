from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, status
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from enum import Enum

from src.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

class TokenType(str, Enum):
    """Типы JWT токенов"""
    ACCESS = "access"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    REFRESH = "refresh"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    user_id: int,
    token_type: TokenType,
    expire_delta: timedelta,
    email: str | None = None,
    extra_data: dict | None = None
) -> str:
    """
    Универсальная функция создания JWT токенов.
    
    Args:
        user_id: ID пользователя
        token_type: Тип токена из TokenType enum
        expire_delta: Время жизни токена
        email: Email (опционально, для password_reset и email_verification)
        extra_data: Дополнительные данные (опционально)
    
    Returns:
        JWT токен строка
    """
    to_encode = {
        "sub": str(user_id),
        "type": token_type.value,
        "exp": datetime.now(timezone.utc) + expire_delta
    }
    
    # Добавляем email если есть
    if email:
        to_encode["email"] = email
    
    # Добавляем дополнительные данные если есть
    if extra_data:
        to_encode.update(extra_data)
    
    return jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )


def create_access_token(data: dict) -> str:
    """
    Создает access токен (15 минут).
    Для обратной совместимости принимает dict с данными.
    """
    user_id = data.get("sub")
    if not user_id:
        raise ValueError("data must contain 'sub' key with user_id")
    
    return create_token(
        user_id=int(user_id),
        token_type=TokenType.ACCESS,
        expire_delta=timedelta(minutes=15)
    )


def create_password_reset_token(user_id: int, email: str) -> str:
    """Создает токен для сброса пароля (1 час)"""
    return create_token(
        user_id=user_id,
        token_type=TokenType.PASSWORD_RESET,
        expire_delta=timedelta(hours=1),
        email=email
    )


def create_email_verification_token(user_id: int, email: str) -> str:
    """Создает токен для подтверждения email (24 часа)"""
    return create_token(
        user_id=user_id,
        token_type=TokenType.EMAIL_VERIFICATION,
        expire_delta=timedelta(days=1),
        email=email
    )


def create_refresh_token(user_id: int) -> str:
    """Создает refresh токен (7 дней)"""
    return create_token(
        user_id=user_id,
        token_type=TokenType.REFRESH,
        expire_delta=timedelta(days=7)
    )


def verify_token(
    token: str, 
    expected_type: TokenType
) -> dict | None:
    """
    Универсальная функция проверки JWT токена конкретного типа.
    
    Args:
        token: JWT токен строка
        expected_type: Ожидаемый тип токена из TokenType enum
    
    Returns:
        dict с данными токена (user_id, email, type) или None если невалиден
    """
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Проверяем тип токена
        if payload.get("type") != expected_type.value:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Возвращаем все данные из токена
        return {
            "user_id": int(user_id),
            "email": payload.get("email"),
            "type": payload.get("type")
        }
        
    except JWTError:
        return None


def verify_password_reset_token(token: str) -> dict | None:
    """
    Проверяет JWT токен сброса пароля.
    Возвращает dict с user_id и email если токен валиден, иначе None.
    """
    token_data = verify_token(token, TokenType.PASSWORD_RESET)
    
    # Дополнительная проверка: email обязателен для reset токенов
    if token_data and not token_data.get("email"):
        return None
    
    return token_data


def verify_refresh_token(token: str) -> dict | None:
    """
    Проверяет JWT refresh токен.
    Возвращает dict с user_id если токен валиден, иначе None.
    """
    return verify_token(token, TokenType.REFRESH)


def verify_email_verification_token(token: str) -> dict | None:
    """
    Проверяет JWT email verification токен.
    Возвращает dict с user_id и email если токен валиден, иначе None.
    """
    token_data = verify_token(token, TokenType.EMAIL_VERIFICATION)
    if token_data and not token_data.get("email"):
        return None
    return token_data


def get_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
):
    if credentials:
        return credentials.credentials
    
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Token not found'
        )
    return token 