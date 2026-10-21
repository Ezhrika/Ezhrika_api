from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.subjects import display_subject


# Структура и проверка данных профиля репетитора в ответах API.
class TutorProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    subject: str
    description: str
    timezone: str

    @field_validator("subject")
    @classmethod
    def normalize_subject_for_display(cls, value: str) -> str:
        return display_subject(value)


# Данные для изменения собственного профиля репетитора.
class TutorProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    subject: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError):
                raise ValueError("Use a valid IANA timezone, for example Asia/Novosibirsk.")
        return value
