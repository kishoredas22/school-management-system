"""Attendance schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import AttendanceStatus


class StudentAttendanceItem(BaseModel):
    """Single student attendance entry."""

    student_id: UUID
    status: AttendanceStatus


class StudentAttendanceCreate(BaseModel):
    """Student attendance batch request."""

    class_id: UUID
    section_id: UUID
    date: date
    attendance: list[StudentAttendanceItem]


class TeacherAttendanceCreate(BaseModel):
    """Teacher attendance request."""

    teacher_id: UUID
    date: date
    status: AttendanceStatus
    note: str | None = None


class AttendanceSummaryItem(BaseModel):
    """Attendance summary payload."""

    entity_id: UUID
    entity_name: str
    present_count: int
    absent_count: int
    leave_count: int
    attendance_percentage: float


class StudentAttendanceRegisterItem(BaseModel):
    """Student attendance register row."""

    student_id: UUID
    student_code: str | None = None
    student_name: str
    status: AttendanceStatus | None = None


class TeacherAttendanceRead(BaseModel):
    """Teacher attendance response row."""

    id: UUID
    teacher_id: UUID
    teacher_name: str
    attendance_date: date
    status: AttendanceStatus
    note: str | None = None
