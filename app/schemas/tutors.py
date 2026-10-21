from pydantic import BaseModel, ConfigDict, Field


# Структура и проверка данных профиля репетитора в ответах API.
class TutorProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    subject: str
    description: str
    timezone: str


# Данные для изменения собственного профиля репетитора.
class TutorProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    subject: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str | None = Field(default=None, max_length=64)
