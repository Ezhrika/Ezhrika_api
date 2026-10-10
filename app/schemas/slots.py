from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Структура и проверка данных слотов репетиторов в ответах API.
class SlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tutor_id: int
    starts_at: datetime
    ends_at: datetime
    status: str


# TODO: Добавить схемы создания и изменения слота с проверкой дат и часового пояса.
