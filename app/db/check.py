from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_engine


# Проверка подключения к PostgreSQL: python -m app.db.check
def main() -> int:
    try:
        engine = get_engine()
    except (RuntimeError, ValueError):
        print("Check DATABASE_URL in .env: expected postgresql+psycopg://user:password@localhost:5432/database.")
        return 1

    try:
        with engine.connect() as connection:
            result = connection.scalar(text("SELECT 1"))
        if result != 1:
            print("The database returned an unexpected result.")
            return 1
    except SQLAlchemyError:
        print("Connection failed. Check that PostgreSQL is running and verify the port, database name, username and password in .env.")
        return 1
    finally:
        engine.dispose()
        get_engine.cache_clear()

    print("PostgreSQL connection successful: SELECT 1 completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
