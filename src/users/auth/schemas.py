from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserOut(BaseModel):
    id: int
    email: EmailStr 
    password: str 
    phone_number: str 
    first_name: str 
    last_name: str 
    is_user: bool
    is_admin: bool
    is_super_admin: bool

class SUserRegister(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта", unique=True)
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
    phone_number: str = Field(..., description="Номер телефона в международном формате, начинающийся с '+'", unique=True)
    first_name: str = Field(..., min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    last_name: str = Field(..., min_length=3, max_length=50, description="Фамилия, от 3 до 50 символов")

    @validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r'^\+\d{5,15}$', value):
            raise ValueError('Номер телефона должен начинаться с "+" и содержать от 5 до 15 цифр')
        return value

class SUserAuth(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")