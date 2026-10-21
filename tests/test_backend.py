import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import jwt
from pydantic_settings.sources import DotEnvSettingsSource
from sqlalchemy import DateTime, create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

# Импорт приложения в тестах не читает локальный .env.
with patch.object(DotEnvSettingsSource, "_read_env_files", return_value={}):
    from app.core.config import settings
    from app.core.security import create_access_token, hash_password
    from app.db.base import Base
    from app.db.session import get_db
    from app.main import app
    from app.models.booking import Booking
    from app.models.notification import Notification
    from app.models.slot import Slot
    from app.models.student import StudentProfile
    from app.models.tutor import TutorProfile
    from app.models.user import User

from fastapi.testclient import TestClient


# SQLite теряет часовой пояс при чтении DateTime; тестовый тип восстанавливает UTC.
class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("password123")
        cls.original_datetime_types = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, DateTime):
                    cls.original_datetime_types.append((column, column.type))
                    column.type = UTCDateTime(timezone=True)

    @classmethod
    def tearDownClass(cls):
        for column, original_type in cls.original_datetime_types:
            column.type = original_type

    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)

        def test_db():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.engine.dispose)
        self.enterContext(patch.object(settings, "debug", False))
        self.enterContext(patch.object(settings, "guest_confirmation_minutes", 15))
        self.enterContext(patch("app.services.email.get_engine", return_value=self.engine))
        self.send_email = self.enterContext(patch("app.services.email.send_raw_email", return_value=True))
        self.client = self.enterContext(TestClient(app))
        self.future = datetime.now(timezone.utc) + timedelta(days=3)
        with Session(self.engine) as db:
            users = [User(email=email, role=role, password_hash=self.password_hash) for email, role in [
                ("tutor@example.org", "tutor"), ("student@example.org", "student"),
                ("other@example.org", "student"), ("other-tutor@example.org", "tutor"),
            ]]
            db.add_all(users)
            db.flush()
            db.add_all([
                TutorProfile(user_id=users[0].id, name="Tutor", subject="Math"),
                StudentProfile(user_id=users[1].id, name="Student"),
                StudentProfile(user_id=users[2].id, name="Other"),
                TutorProfile(user_id=users[3].id, name="Other tutor", subject="Physics"),
            ])
            db.flush()
            tutor_id = db.scalar(select(TutorProfile.id).where(TutorProfile.user_id == users[0].id))
            self.tutor_id = tutor_id
            self.auth = {user.role + str(i): {"Authorization": "Bearer " + create_access_token({"sub": str(user.id)})}
                         for i, user in enumerate(users)}
            db.add_all([
                Slot(tutor_id=tutor_id, starts_at=self.future, ends_at=self.future + timedelta(hours=1)),
                Slot(tutor_id=tutor_id, starts_at=self.future + timedelta(hours=2), ends_at=self.future + timedelta(hours=3)),
                Slot(tutor_id=tutor_id, starts_at=self.future - timedelta(days=5), ends_at=self.future - timedelta(days=5) + timedelta(hours=1)),
            ])
            db.commit()

    def guest_booking(self, slot_id=1):
        response = self.client.post("/api/v1/bookings", json={
            "slot_id": slot_id, "student_name": "Guest", "student_email": "guest@example.org",
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def student_booking(self):
        response = self.client.post("/api/v1/bookings", json={"slot_id": 1}, headers=self.auth["student1"])
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def links(self, booking_id):
        with Session(self.engine) as db:
            body = db.scalar(select(Notification.body).where(Notification.booking_id == booking_id))
        return [line for line in body.splitlines() if line.startswith("http")]

    def age_booking(self, booking_id):
        with Session(self.engine) as db:
            db.get(Booking, booking_id).created_at = datetime.now(timezone.utc) - timedelta(minutes=16)
            db.commit()

    def test_debug_routes_require_only_debug_flag(self):
        paths = ["users", "students", "bookings", "notifications", "slots"]
        for path in paths:
            self.assertEqual(self.client.get("/api/v1/" + path).status_code, 404)
        self.assertEqual(self.client.post("/api/v1/notifications/process").status_code, 404)
        with patch.object(settings, "debug", True):
            for path in paths:
                self.assertEqual(self.client.get("/api/v1/" + path).status_code, 200)
            self.assertEqual(self.client.post("/api/v1/notifications/process").status_code, 200)

    def test_overlong_registration_passwords_return_422(self):
        for password in ["a" * 73, "\u044f" * 40]:
            response = self.client.post("/api/v1/auth/register", json={
                "email": "new@example.org", "password": password, "role": "student",
            })
            self.assertEqual(response.status_code, 422)

    def test_bcrypt_limit_passwords_register_and_login(self):
        for i, password in enumerate(["a" * 72, "\u044f" * 36]):
            email = f"new{i}@example.org"
            response = self.client.post("/api/v1/auth/register", json={
                "email": email, "password": password, "role": "student",
            })
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(self.client.post("/api/v1/auth/login", json={"email": email, "password": password}).status_code, 200)
            self.assertEqual(self.client.post("/api/v1/auth/login", json={"email": email, "password": password + "x"}).status_code, 401)

    def test_existing_password_still_works(self):
        response = self.client.post("/api/v1/auth/login", json={"email": "student@example.org", "password": "password123"})
        self.assertEqual(response.status_code, 200)

    def test_guest_gets_two_links_and_get_does_not_confirm(self):
        booking = self.guest_booking()
        self.assertEqual(booking["status"], "pending")
        confirm_url, cancel_url = self.links(booking["id"])
        self.assertIn(booking["cancel_token"], cancel_url)
        self.assertEqual(self.client.get(confirm_url).status_code, 200)
        self.assertEqual(self.client.get(cancel_url).status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Booking, booking["id"]).status, "pending")
            self.assertEqual(db.get(Slot, 1).status, "pending")
        self.assertTrue(self.send_email.called)
        self.assertEqual(self.client.post(confirm_url).status_code, 200)
        self.assertEqual(self.client.post(confirm_url).status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Booking, booking["id"]).status, "active")
            self.assertEqual(db.get(Slot, 1).status, "booked")
        self.assertEqual(self.client.post(cancel_url).status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "open")

    def test_confirmation_token_cannot_authenticate(self):
        booking = self.guest_booking()
        token = parse_qs(urlsplit(self.links(booking["id"])[0]).query)["token"][0]
        response = self.client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 401)

    def test_wrong_confirmation_token_rejected(self):
        for token in ["invalid", create_access_token({"sub": "1"})]:
            response = self.client.post("/api/v1/bookings/confirm-by-token", json={"token": token})
            self.assertEqual(response.status_code, 400)

    def test_expired_booking_released_on_public_schedule(self):
        booking = self.guest_booking()
        self.age_booking(booking["id"])
        response = self.client.get(f"/api/v1/tutors/{self.tutor_id}/slots")
        self.assertIn(1, [slot["id"] for slot in response.json()])
        with Session(self.engine) as db:
            self.assertEqual(db.get(Booking, booking["id"]).status, "expired")
        self.assertEqual(self.client.post(self.links(booking["id"])[0]).status_code, 409)

    def test_expired_confirmation_returns_410_and_releases_slot(self):
        booking = self.guest_booking()
        self.age_booking(booking["id"])
        response = self.client.post(self.links(booking["id"])[0])
        self.assertEqual(response.status_code, 410)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "open")

    def test_expired_signed_token_rejected(self):
        booking = self.guest_booking()
        self.age_booking(booking["id"])
        token = parse_qs(urlsplit(self.links(booking["id"])[0]).query)["token"][0]
        data = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
        data["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        token = jwt.encode(data, settings.secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
        response = self.client.post("/api/v1/bookings/confirm-by-token", json={"token": token})
        self.assertEqual(response.status_code, 410)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "open")

    def test_expired_confirmation_email_not_sent_on_retry(self):
        from app.services.email import process_pending_notifications

        booking = self.guest_booking()
        self.age_booking(booking["id"])
        self.send_email.reset_mock()
        with Session(self.engine) as db:
            notification = db.scalar(select(Notification).where(Notification.booking_id == booking["id"]))
            notification.status = "pending"
            db.commit()
            process_pending_notifications(db)
            self.assertEqual(notification.status, "cancelled")
        self.send_email.assert_not_called()

    def test_sent_notification_not_sent_twice(self):
        from app.services.email import process_notification

        booking = self.guest_booking()
        self.send_email.reset_mock()
        with Session(self.engine) as db:
            notification = db.scalar(select(Notification).where(Notification.booking_id == booking["id"]))
            self.assertFalse(process_notification(db, notification))
        self.send_email.assert_not_called()

    def test_old_tokens_do_not_change_replacement_booking(self):
        old = self.guest_booking()
        links = self.links(old["id"])
        self.age_booking(old["id"])
        new = self.guest_booking()
        self.assertNotEqual(new["id"], old["id"])
        self.assertEqual(self.client.post(links[0]).status_code, 409)
        self.assertEqual(self.client.post(links[1]).status_code, 400)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "pending")
            self.assertEqual(db.get(Booking, new["id"]).status, "pending")

    def test_cancelled_booking_cannot_be_confirmed(self):
        booking = self.guest_booking()
        confirm_url, cancel_url = self.links(booking["id"])
        self.assertEqual(self.client.post(cancel_url).status_code, 200)
        self.assertEqual(self.client.post(confirm_url).status_code, 409)

    def test_student_booking_and_enriched_cabinet_response(self):
        booking = self.student_booking()
        self.assertEqual(booking["status"], "active")
        response = self.client.get("/api/v1/bookings/my", headers=self.auth["student1"])
        item = response.json()[0]
        for key in ["starts_at", "ends_at", "tutor_id", "tutor_name", "subject"]:
            self.assertIn(key, item)
        self.assertEqual(item["tutor_name"], "Tutor")
        self.assertEqual(self.client.get("/api/v1/bookings/my", headers=self.auth["student2"]).json(), [])
        self.assertEqual(self.client.get("/api/v1/bookings/tutor", headers=self.auth["tutor0"]).json()[0]["id"], booking["id"])
        self.assertEqual(self.client.post(f'/api/v1/bookings/{booking["id"]}/cancel', headers=self.auth["student2"]).status_code, 403)

    def test_delete_slot_with_booking_history_closes_it(self):
        booking = self.student_booking()
        self.assertEqual(self.client.post(f'/api/v1/bookings/{booking["id"]}/cancel', headers=self.auth["student1"]).status_code, 200)
        self.assertEqual(self.client.delete("/api/v1/slots/1", headers=self.auth["tutor0"]).status_code, 204)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "cancelled")
            self.assertEqual(db.get(Booking, booking["id"]).status, "cancelled")
        self.assertEqual(self.client.get("/api/v1/bookings/my", headers=self.auth["student1"]).status_code, 200)

    def test_delete_empty_slot_removes_it(self):
        self.assertEqual(self.client.delete("/api/v1/slots/1", headers=self.auth["tutor0"]).status_code, 204)
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Slot, 1))

    def test_pending_slot_cannot_be_deleted_or_double_booked(self):
        self.guest_booking()
        self.assertEqual(self.client.delete("/api/v1/slots/1", headers=self.auth["tutor0"]).status_code, 400)
        response = self.client.post("/api/v1/bookings", json={"slot_id": 1}, headers=self.auth["student1"])
        self.assertEqual(response.status_code, 409)

    def test_public_schedule_excludes_past_slots(self):
        response = self.client.get(f"/api/v1/tutors/{self.tutor_id}/slots")
        self.assertEqual([slot["id"] for slot in response.json()], [1, 2])

    def test_timezone_validated(self):
        for value in ["Not/A_Timezone", "", "../UTC"]:
            response = self.client.patch("/api/v1/tutors/me", json={"timezone": value}, headers=self.auth["tutor0"])
            self.assertEqual(response.status_code, 422)
        response = self.client.patch("/api/v1/tutors/me", json={"timezone": "Asia/Novosibirsk"}, headers=self.auth["tutor0"])
        self.assertEqual(response.status_code, 200)

    def test_invalid_auth_does_not_silently_create_guest_booking(self):
        for authorization in ["Bearer invalid", "Basic abc", "Bearer"]:
            response = self.client.post("/api/v1/bookings", json={
                "slot_id": 1, "student_name": "Guest", "student_email": "guest@example.org",
            }, headers={"Authorization": authorization})
            self.assertEqual(response.status_code, 401)

    def test_overlapping_slots_rejected(self):
        response = self.client.post("/api/v1/slots", json={
            "starts_at": (self.future + timedelta(minutes=30)).isoformat(),
            "ends_at": (self.future + timedelta(minutes=90)).isoformat(),
        }, headers=self.auth["tutor0"])
        self.assertEqual(response.status_code, 409)

    def test_tutor_cancellation_closes_slot(self):
        booking = self.student_booking()
        response = self.client.post(f'/api/v1/bookings/{booking["id"]}/cancel-by-tutor', headers=self.auth["tutor0"])
        self.assertEqual(response.status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Slot, 1).status, "cancelled")


if __name__ == "__main__":
    unittest.main()
