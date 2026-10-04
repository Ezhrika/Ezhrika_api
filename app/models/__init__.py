"""ORM-модели consultations_v2, использующие существующий app.db.base.Base.

Импорт app.models регистрирует все 32 таблицы; подключения к БД здесь нет.
Это новая схема, не совместимый адаптер старых роутеров или миграция данных.
"""
from app.db.base import Base

from .people.models import Person
from .users.models import User
from .user_roles.models import UserRoleAssignment
from .teachers.models import Teacher
from .students.models import Student
from .departments.models import Department
from .academic_groups.models import AcademicGroup
from .buildings.models import Building
from .classrooms.models import Classroom
from .subjects.models import Subject
from .teacher_subjects.models import TeacherSubject
from .bell_schedules.models import BellSchedule
from .period_slots.models import PeriodSlot
from .timetable_events.models import TimetableEvent
from .timetable_event_teachers.models import TimetableEventTeacher
from .timetable_event_groups.models import TimetableEventGroup
from .room_reservations.models import RoomReservation
from .consultations.models import Consultation
from .consultation_allowed_groups.models import ConsultationAllowedGroup
from .consultation_registrations.models import ConsultationRegistration
from .consultation_overlap_permissions.models import ConsultationOverlapPermission
from .consultation_requests.models import ConsultationRequest
from .teacher_scheduling_settings.models import TeacherSchedulingSettings
from .teacher_availability_rules.models import TeacherAvailabilityRule
from .teacher_availability_exceptions.models import TeacherAvailabilityException
from .schedule_sources.models import ScheduleSource
from .schedule_imports.models import ScheduleImport
from .schedule_event_sources.models import ScheduleEventSource
from .schedule_conflicts.models import ScheduleConflict
from .ai_proposals.models import AIProposal
from .notifications.models import Notification
from .video_meetings.models import VideoMeeting

from .enums import (
    BoardType,
    ScreenType,
    UserRole,
    TimetableKind,
    TimetableStatus,
    TimetableVisibility,
    ReservationStatus,
    ConsultationFormat,
    AudienceMode,
    ConsultationStatus,
    RegistrationStatus,
    ConsultationRequestStatus,
    AvailabilityKind,
    AvailabilityExceptionKind,
    ScheduleSourceKind,
    ScheduleSourceAuthority,
    ScheduleImportStatus,
    ConflictKind,
    ConflictStatus,
    AIProposalKind,
    AIProposalStatus,
)

from ._events import register_model_events as _register_model_events

_register_model_events()
del _register_model_events

__all__ = [
    "BoardType",
    "ScreenType",
    "Base",
    "Person",
    "User",
    "UserRoleAssignment",
    "Teacher",
    "Student",
    "Department",
    "AcademicGroup",
    "Building",
    "Classroom",
    "Subject",
    "TeacherSubject",
    "BellSchedule",
    "PeriodSlot",
    "TimetableEvent",
    "TimetableEventTeacher",
    "TimetableEventGroup",
    "RoomReservation",
    "Consultation",
    "ConsultationAllowedGroup",
    "ConsultationRegistration",
    "ConsultationOverlapPermission",
    "ConsultationRequest",
    "TeacherSchedulingSettings",
    "TeacherAvailabilityRule",
    "TeacherAvailabilityException",
    "ScheduleSource",
    "ScheduleImport",
    "ScheduleEventSource",
    "ScheduleConflict",
    "AIProposal",
    "Notification",
    "VideoMeeting",
    "UserRole",
    "TimetableKind",
    "TimetableStatus",
    "TimetableVisibility",
    "ReservationStatus",
    "ConsultationFormat",
    "AudienceMode",
    "ConsultationStatus",
    "RegistrationStatus",
    "ConsultationRequestStatus",
    "AvailabilityKind",
    "AvailabilityExceptionKind",
    "ScheduleSourceKind",
    "ScheduleSourceAuthority",
    "ScheduleImportStatus",
    "ConflictKind",
    "ConflictStatus",
    "AIProposalKind",
    "AIProposalStatus",
]
