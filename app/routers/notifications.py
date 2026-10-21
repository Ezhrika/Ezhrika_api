from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.debug import require_debug
from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notifications import NotificationRead
from app.services.email import process_pending_notifications


router = APIRouter(
    prefix="/api/v1/notifications", tags=["notifications"],
    dependencies=[Depends(require_debug)],
)


# Получение всех уведомлений из БД (для локальной отладки).
@router.get("", response_model=list[NotificationRead], summary="Get all notifications")
def get_all_notifications(db: Annotated[Session, Depends(get_db)]) -> list[Notification]:
    return list(db.scalars(select(Notification).order_by(Notification.id)).all())


# Запуск обработки очереди ожидающих отправки писем.
@router.post("/process", summary="Process pending email notifications")
def process_queue(db: Annotated[Session, Depends(get_db)]) -> dict[str, int]:
    count = process_pending_notifications(db)
    return {"processed": count}
