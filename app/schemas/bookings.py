from datetime import datetime

from pydantic import AliasPath, BaseModel, ConfigDict, EmailStr, Field
from pydantic import field_validator

from app.core.subjects import display_subject


# Структура и проверка данных записей на занятия в ответах API.
class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    slot_id: int
    starts_at: datetime = Field(validation_alias=AliasPath("slot", "starts_at"))
    ends_at: datetime = Field(validation_alias=AliasPath("slot", "ends_at"))
    tutor_id: int = Field(validation_alias=AliasPath("slot", "tutor_id"))
    tutor_name: str = Field(validation_alias=AliasPath("slot", "tutor", "name"))
    subject: str = Field(validation_alias=AliasPath("slot", "tutor", "subject"))
    student_id: int | None
    student_name: str
    student_email: str
    question: str
    status: str
    created_at: datetime

    @field_validator("subject")
    @classmethod
    def normalize_subject_for_display(cls, value: str) -> str:
        return display_subject(value)


# Ответ при успешной записи с возможным токеном отмены для гостя.
class BookingGuestResponse(BookingRead):
    cancel_token: str | None = None


# Данные для бронирования занятия учеником или гостем.
class BookingCreate(BaseModel):
    slot_id: int
    student_name: str | None = Field(default=None, max_length=100)
    student_email: EmailStr | None = None
    question: str = Field(default="", max_length=1000)


# Запрос на отмену занятия по разовому токену гостя.
class CancelByTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


# Запрос на подтверждение гостевой записи токеном из письма.
class ConfirmByTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=2048)
