from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Структура и проверка данных аккаунтов пользователей в ответах API.
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    created_at: datetime


# Данные для регистрации нового пользователя.
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["tutor", "student"]
    name: str = Field(default="", max_length=100)
    subject: str = Field(default="", max_length=100)


# Данные для входа пользователя по email и паролю.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Ответ сервера с токеном доступа.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
