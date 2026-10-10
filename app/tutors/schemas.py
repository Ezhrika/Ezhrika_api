# Данные профиля репетитора в ответах API.
# TODO: Добавить схемы создания и изменения профиля с проверкой входных данных.

from pydantic import BaseModel, ConfigDict


class TutorProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject: str
    description: str
    timezone: str
