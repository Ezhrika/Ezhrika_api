from pydantic import BaseModel, ConfigDict


# Структура и проверка данных профиля в ответах API.
# TODO: Добавить схемы создания и изменения профиля с проверкой входных данных.
class TutorProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject: str
    description: str
    timezone: str
