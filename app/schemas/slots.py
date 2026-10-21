from datetime import datetime, timezone
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


# Структура и проверка данных слотов репетиторов в ответах API.
class SlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tutor_id: int
    starts_at: datetime
    ends_at: datetime
    status: str


# Данные для создания нового свободного слота репетитора.
class SlotCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        now = datetime.now(timezone.utc)
        start = self.starts_at if self.starts_at.tzinfo else self.starts_at.replace(tzinfo=timezone.utc)
        end = self.ends_at if self.ends_at.tzinfo else self.ends_at.replace(tzinfo=timezone.utc)

        if end <= start:
            raise ValueError("Slot end time must be after start time.")
        if start < now:
            raise ValueError("Slot start time cannot be in the past.")

        self.starts_at = start
        self.ends_at = end
        return self
