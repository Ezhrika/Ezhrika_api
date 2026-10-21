from datetime import datetime, timedelta, timezone
import atexit
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pydantic_settings.sources import DotEnvSettingsSource
from sqlalchemy import DateTime, create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeDecorator

# Отдельный сервер для браузерной проверки. Только временные данные, без локального .env.
with patch.object(DotEnvSettingsSource, "_read_env_files", return_value={}):
    from app.main import app
    from app.core.security import hash_password
    from app.db.base import Base
    from app.db.session import get_db
    from app.models import User, TutorProfile, Slot, Notification


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, DateTime):
            column.type = UTCDateTime(timezone=True)

temporary_directory = TemporaryDirectory(prefix="ezhrika-frontend-")
database_path = Path(temporary_directory.name) / "preview.sqlite"
engine = create_engine(f"sqlite:///{database_path.as_posix()}", connect_args={"check_same_thread": False, "timeout": 10})


def cleanup():
    engine.dispose()
    temporary_directory.cleanup()


atexit.register(cleanup)


@event.listens_for(engine, "connect")
def foreign_keys(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")


Base.metadata.create_all(engine)


def preview_db():
    with Session(engine) as db:
        yield db


app.dependency_overrides[get_db] = preview_db
patch("app.services.email.get_engine", return_value=engine).start()
patch("app.services.email.send_raw_email", return_value=True).start()

with Session(engine) as db:
    user = User(email="preview-tutor@example.org", password_hash=hash_password("preview-password"), role="tutor")
    db.add(user)
    db.flush()
    tutor = TutorProfile(user_id=user.id, name="Анна Смирнова", subject="Математика", description="Помогаю разобраться в математике и почувствовать уверенность перед экзаменами. На занятиях разбираем сложные темы простыми шагами и много практикуемся.", timezone="Asia/Novosibirsk")
    db.add(tutor)
    db.flush()
    tomorrow = datetime.now(timezone.utc).replace(hour=3, minute=0, second=0, microsecond=0) + timedelta(days=1)
    for day in range(5):
        for hour in [0, 2, 7]:
            start = tomorrow + timedelta(days=day, hours=hour)
            db.add(Slot(tutor_id=tutor.id, starts_at=start, ends_at=start + timedelta(hours=1)))
    db.commit()


@app.get("/__qa/mail", include_in_schema=False)
def preview_mail():
    with Session(engine) as db:
        return list(db.scalars(select(Notification.body).order_by(Notification.id)).all())
