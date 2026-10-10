from pydantic import BaseModel, ConfigDict


# Структура и проверка данных профиля ученика в ответах API.
class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str


# TODO: Добавить схемы создания и изменения профиля с проверкой имени.
