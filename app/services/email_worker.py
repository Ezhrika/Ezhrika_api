from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.services.email import process_pending_notifications


# Консольный воркер отправки писем из очереди: python -m app.services.email_worker
def main() -> int:
    with Session(get_engine()) as db:
        count = process_pending_notifications(db)
        print(f"Processed {count} pending email notification(s).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
