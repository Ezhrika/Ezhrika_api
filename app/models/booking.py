from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# Записи зарегистрированных учеников и гостей на занятия.
class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("student_profiles.id")) # Для гостевой записи профиль ученика отсутствует.
    student_name: Mapped[str] = mapped_column(String(100))
    student_email: Mapped[str] = mapped_column(String(254))
    question: Mapped[str] = mapped_column(Text, server_default="")
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    cancel_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True) # Гость отменяет запись по ссылке, зарегистрированный ученик — в кабинете.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
