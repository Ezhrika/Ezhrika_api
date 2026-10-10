from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Структура и проверка данных уведомлений в ответах API.
class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    recipient_email: str
    subject: str
    status: str
    attempts: int
    created_at: datetime


# TODO: Добавить проверку данных уведомлений при постановке письма в очередь.
