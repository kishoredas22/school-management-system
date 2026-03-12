"""Student models."""

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import StudentStatus


class Student(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Student master record."""

    __tablename__ = "students"

    student_id: Mapped[str | None] = mapped_column(String(50), index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    guardian_name: Mapped[str | None] = mapped_column(String(150))
    guardian_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, native_enum=False),
        default=StudentStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    academic_records = relationship("StudentAcademicRecord", back_populates="student", cascade="all, delete-orphan")
    fee_payments = relationship("FeePayment", back_populates="student")
    attendance_records = relationship("StudentAttendance", back_populates="student")


class StudentAcademicRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Academic-year-specific student record."""

    __tablename__ = "student_academic_records"
    __table_args__ = (Index("idx_student_year", "student_id", "academic_year_id"),)

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(ForeignKey("sections.id"), nullable=False, index=True)
    promotion_status: Mapped[str | None] = mapped_column(String(20))

    student = relationship("Student", back_populates="academic_records")
    academic_year = relationship("AcademicYear", back_populates="student_records")
    class_room = relationship("ClassRoom", back_populates="student_records")
    section = relationship("Section", back_populates="student_records")
