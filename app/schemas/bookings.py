from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Структура и проверка данных записей на занятия в ответах API.
class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slot_id: int
    student_id: int | None
    student_name: str
    student_email: str
    question: str
    status: str
    created_at: datetime


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
    token: str = Field(min_length=1)
