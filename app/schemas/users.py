from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Структура и проверка данных аккаунтов репетиторов в ответах API.
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


# TODO: Добавить схемы регистрации и входа с проверкой email и пароля.
