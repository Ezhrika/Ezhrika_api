from app.db.session import get_db
from app.services.email import process_pending_notifications


# Консольный воркер отправки писем из очереди: python -m app.services.email_worker
def main() -> int:
    db = next(get_db())
    try:
        count = process_pending_notifications(db)
        print(f"Processed {count} pending email notification(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
