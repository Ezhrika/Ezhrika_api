from pydantic import BaseModel, ConfigDict, Field


# Структура и проверка данных профиля ученика в ответах API.
class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str


# Данные для изменения собственного профиля ученика.
class StudentProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
