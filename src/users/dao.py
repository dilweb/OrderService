from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from src.users.models.user import User
from src.users.auth.schemas import SUserRegister, UserOut
from src.users.auth.auth import get_password_hash 

class UserDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> UserOut | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, id: int) -> UserOut | None:
        result = await self.session.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_users_list(self) -> List[UserOut] | None:
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def update_user(self, user_id: int, **kwargs) -> User | None:
        """
        Универсальное обновление полей пользователя.
        
        Пример:
            await update_user(user_id=1, is_admin=True)
            await update_user(user_id=1, first_name="Новое имя", is_admin=True)
        """
        user = await self.get_user_by_id(id=user_id)
        if not user:
            return None
        
        # Применяем все переданные изменения
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
            else:
                raise ValueError(f"User модель не имеет поля '{key}'")
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_user(self, user: SUserRegister) -> User | None:
        user = User(
        email=user.email,
        password=get_password_hash(user.password),
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
    )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user_id: int, new_password: str) -> None:
        """Обновление пароля пользователя"""
        hashed_password = get_password_hash(new_password)
        await self.update_user(user_id=user_id, password=hashed_password)


    async def user_email_verification(self, user_id: int) -> None:
        """Подтверждение email"""
        await self.update_user(user_id=user_id, is_email_verified=True)


    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя по id. Возвращает True если удалён, False если не найден."""
        user = await self.get_user_by_id(id=user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True
 