from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import get_engine
from app.models.booking import Booking  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.slot import Slot  # noqa: F401
from app.models.student import StudentProfile  # noqa: F401
from app.models.tutor import TutorProfile  # noqa: F401
from app.models.user import User  # noqa: F401


# Создание всех таблиц в PostgreSQL: python -m app.db.init_db
def main() -> int:
    try:
        engine = get_engine()
    except (RuntimeError, ValueError):
        print("Check DATABASE_URL in .env: expected postgresql+psycopg://user:password@localhost:5432/database.")
        return 1

    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError:
        print("Database initialization failed. Check PostgreSQL connection.")
        return 1
    finally:
        engine.dispose()
        get_engine.cache_clear()

    print("Database tables created successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
