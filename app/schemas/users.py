from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.subjects import require_subject


# Структура и проверка данных аккаунтов пользователей в ответах API.
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    created_at: datetime


# Имя профиля доступно самому владельцу аккаунта для шапки сайта.
class CurrentUserRead(UserRead):
    name: str


# Данные для регистрации нового пользователя.
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal["tutor", "student"]
    name: str = Field(default="", max_length=100)
    subject: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def validate_tutor_subject(self):
        if self.role == "tutor":
            self.subject = require_subject(self.subject)
        return self

    @field_validator("password")
    @classmethod
    def validate_password_characters(cls, value: str) -> str:
        if not all("!" <= character <= "~" for character in value):
            raise ValueError("Use Latin letters, digits and symbols without spaces.")
        return value


# Данные для входа пользователя по email и паролю.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Ответ сервера с токеном доступа.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
