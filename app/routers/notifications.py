from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notifications import NotificationRead


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# Получение всех уведомлений из БД.
@router.get("", response_model=list[NotificationRead], summary="Get all notifications")
def get_all_notifications(db: Annotated[Session, Depends(get_db)]) -> list[Notification]:
    return list(db.scalars(select(Notification).order_by(Notification.id)).all())


# TODO: Реализовать обработчик очереди и повторные попытки отправки; ограничить доступ к списку.
