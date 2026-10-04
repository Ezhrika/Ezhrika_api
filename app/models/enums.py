"""Константы значений CHECK. Из БД приходят строки, не Enum-объекты.

UserRole остаётся enum; строку таблицы user_roles представляет UserRoleAssignment.
room_type и board_type в новой DBML — свободные VARCHAR, не перечисления.
BoardType/ScreenType сохранены только для старых импортов, не для ограничений БД.
"""
import enum


class UserRole(str, enum.Enum):
    student = 'student'
    teacher = 'teacher'
    admin = 'admin'


class TimetableKind(str, enum.Enum):
    lecture = 'lecture'
    practice = 'practice'
    lab = 'lab'
    exam = 'exam'
    retake = 'retake'
    other = 'other'


class TimetableStatus(str, enum.Enum):
    scheduled = 'scheduled'
    cancelled = 'cancelled'


class TimetableVisibility(str, enum.Enum):
    shared = 'shared'
    personal = 'personal'


class ReservationStatus(str, enum.Enum):
    active = 'active'
    conflicted = 'conflicted'
    released = 'released'


class ConsultationFormat(str, enum.Enum):
    onsite = 'onsite'
    online = 'online'
    hybrid = 'hybrid'


class AudienceMode(str, enum.Enum):
    all_students = 'all_students'
    selected_groups = 'selected_groups'


class ConsultationStatus(str, enum.Enum):
    draft = 'draft'
    published = 'published'
    cancelled = 'cancelled'
    completed = 'completed'


class RegistrationStatus(str, enum.Enum):
    confirmed = 'confirmed'
    cancelled = 'cancelled'
    attended = 'attended'
    no_show = 'no_show'


class ConsultationRequestStatus(str, enum.Enum):
    pending = 'pending'
    planned = 'planned'
    rejected = 'rejected'
    cancelled = 'cancelled'


class AvailabilityKind(str, enum.Enum):
    available = 'available'
    unavailable = 'unavailable'
    preferred = 'preferred'
    avoided = 'avoided'


class AvailabilityExceptionKind(str, enum.Enum):
    available = 'available'
    unavailable = 'unavailable'


class ScheduleSourceKind(str, enum.Enum):
    website = 'website'
    file = 'file'
    manual = 'manual'


class ScheduleSourceAuthority(str, enum.Enum):
    official = 'official'
    user_provided = 'user_provided'


class ScheduleImportStatus(str, enum.Enum):
    pending = 'pending'
    review = 'review'
    applied = 'applied'
    failed = 'failed'
    rejected = 'rejected'


class ConflictKind(str, enum.Enum):
    room_busy = 'room_busy'
    teacher_busy = 'teacher_busy'
    outside_reservation = 'outside_reservation'
    availability_changed = 'availability_changed'
    source_changed = 'source_changed'


class ConflictStatus(str, enum.Enum):
    open = 'open'
    resolved = 'resolved'
    dismissed = 'dismissed'


class AIProposalKind(str, enum.Enum):
    availability_change = 'availability_change'
    consultation_create = 'consultation_create'
    consultation_change = 'consultation_change'
    room_change = 'room_change'


class AIProposalStatus(str, enum.Enum):
    pending = 'pending'
    applied = 'applied'
    rejected = 'rejected'
    obsolete = 'obsolete'


# Legacy import compatibility only. New columns do not use these enum types.
class BoardType(str, enum.Enum):
    chalk = "chalk"
    marker = "marker"
    interactive = "interactive"


class ScreenType(str, enum.Enum):
    none = "none"
    projector = "projector"
    tv = "tv"
    interactive = "interactive"


__all__ = [
    "BoardType",
    "ScreenType",
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
