from email.message import EmailMessage
import smtplib
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_engine
from app.models.booking import Booking
from app.models.notification import Notification
from app.services.bookings import expire_pending_bookings


import sys

# Отправка одного email-сообщения через SMTP или вывод в консоль для разработки.
def send_raw_email(recipient: str, subject: str, body: str) -> bool:
    if not settings.smtp_host:
        log_line = f"[CONSOLE EMAIL] To: {recipient} | Subject: {subject}\n{body}\n{'-' * 40}\n"
        if hasattr(sys.stdout, "buffer") and sys.stdout.buffer:
            sys.stdout.buffer.write(log_line.encode("utf-8", errors="replace"))
            sys.stdout.flush()
        else:
            print(log_line.encode("ascii", errors="replace").decode("ascii"))
        return True

    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password.get_secret_value():
                server.login(
                    settings.smtp_user,
                    settings.smtp_password.get_secret_value(),
                )
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] Failed to send email to {recipient}: {exc}")
        return False


# Обработка одного уведомления с обновлением статуса и счётчика попыток.
def process_notification(db: Session, notification: Notification) -> bool:
    notification = db.scalar(
        select(Notification).where(Notification.id == notification.id)
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    )
    if notification is None or notification.status != "pending":
        return False
    booking = db.get(Booking, notification.booking_id)
    if booking is not None and booking.status == "expired":
        notification.status = "cancelled"
        db.commit()
        return False
    if notification.attempts >= settings.max_notification_attempts:
        notification.status = "failed"
        db.commit()
        return False
    success = send_raw_email(
        recipient=notification.recipient_email,
        subject=notification.subject,
        body=notification.body,
    )
    notification.attempts += 1
    if success:
        notification.status = "sent"
    elif notification.attempts >= settings.max_notification_attempts:
        notification.status = "failed"

    db.add(notification)
    db.commit()
    db.refresh(notification)
    return success


# Пакетная обработка всех ожидающих отправки уведомлений из очереди.
def process_pending_notifications(db: Session, limit: int = 50) -> int:
    expire_pending_bookings(db)
    db.commit()
    notifications: Sequence[Notification] = db.scalars(
        select(Notification)
        .where(
            Notification.status == "pending",
            Notification.attempts < settings.max_notification_attempts,
        )
        .order_by(Notification.created_at)
        .limit(limit)
    ).all()

    processed_count = 0
    for notif in notifications:
        process_notification(db, notif)
        processed_count += 1

    return processed_count


# Фоновая задача отправки уведомления по идентификатору для FastAPI BackgroundTasks.
def send_notification_background(notification_id: int) -> None:
    with Session(get_engine()) as db:
        notification = db.get(Notification, notification_id)
        if notification and notification.status == "pending":
            process_notification(db, notification)
