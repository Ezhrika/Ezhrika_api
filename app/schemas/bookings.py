from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


# TODO: Добавить схемы записи и отмены с проверкой имени и email ученика.
