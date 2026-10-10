# Описание таблицы профилей репетиторов.
# TODO: Добавить связь профиля с аккаунтом и уникальное имя для публичной ссылки.

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, server_default="")
    timezone: Mapped[str] = mapped_column(String(64), server_default="UTC")
