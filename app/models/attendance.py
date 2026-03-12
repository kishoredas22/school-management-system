"""Attendance models."""

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AttendanceStatus


class StudentAttendance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Student attendance record."""

    __tablename__ = "student_attendance"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus, native_enum=False), nullable=False)
    marked_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    student = relationship("Student", back_populates="attendance_records")
    academic_year = relationship("AcademicYear", back_populates="student_attendance")
    marker = relationship("User")


class TeacherAttendance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Teacher attendance record."""

    __tablename__ = "teacher_attendance"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus, native_enum=False), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))

    teacher = relationship("Teacher", back_populates="attendance_records")
    academic_year = relationship("AcademicYear", back_populates="teacher_attendance")
