"""Teacher, assignment, contract, and payment models."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentMode


class Teacher(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Teacher master record."""

    __tablename__ = "teachers"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    assignments = relationship("TeacherClassAssignment", back_populates="teacher", cascade="all, delete-orphan")
    subject_assignments = relationship("TeacherSubjectAssignment", back_populates="teacher", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="teacher")
    contracts = relationship("TeacherContract", back_populates="teacher", cascade="all, delete-orphan")
    payments = relationship("TeacherPayment", back_populates="teacher")
    attendance_records = relationship("TeacherAttendance", back_populates="teacher")
    user_accounts = relationship("User", back_populates="teacher_profile")


class TeacherClassAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Internal table to support class-scoped teacher access."""

    __tablename__ = "teacher_class_assignments"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("sections.id"))
    academic_year_id: Mapped[str | None] = mapped_column(ForeignKey("academic_years.id"))

    teacher = relationship("Teacher", back_populates="assignments")
    class_room = relationship("ClassRoom", back_populates="teacher_assignments")
    section = relationship("Section", back_populates="teacher_assignments")


class TeacherContract(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Year-specific teacher contract."""

    __tablename__ = "teacher_contracts"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    yearly_contract_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monthly_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    teacher = relationship("Teacher", back_populates="contracts")
    academic_year = relationship("AcademicYear", back_populates="teacher_contracts")
    payments = relationship("TeacherPayment", back_populates="contract")


class TeacherPayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Teacher salary payment record."""

    __tablename__ = "teacher_payments"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("teacher_contracts.id"), nullable=False, index=True)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode, native_enum=False), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    teacher = relationship("Teacher", back_populates="payments")
    contract = relationship("TeacherContract", back_populates="payments")
