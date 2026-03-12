"""Academic management models."""

from datetime import date, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Subject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """School subject master."""

    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    teacher_subject_assignments = relationship("TeacherSubjectAssignment", back_populates="subject")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")
    exam_subjects = relationship("ExamSubject", back_populates="subject")


class TeacherSubjectAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Teacher to subject mapping for a class/section/year."""

    __tablename__ = "teacher_subject_assignments"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "class_id",
            "section_id",
            "subject_id",
            name="uq_teacher_subject_scope",
        ),
    )

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("sections.id"))

    teacher = relationship("Teacher", back_populates="subject_assignments")
    subject = relationship("Subject", back_populates="teacher_subject_assignments")
    academic_year = relationship("AcademicYear")
    class_room = relationship("ClassRoom")
    section = relationship("Section")


class TimetableEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Class timetable row."""

    __tablename__ = "timetable_entries"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "class_id",
            "section_id",
            "weekday",
            "period_label",
            name="uq_timetable_scope_slot",
        ),
    )

    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("sections.id"))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    weekday: Mapped[str] = mapped_column(String(12), nullable=False)
    period_label: Mapped[str] = mapped_column(String(40), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room_label: Mapped[str | None] = mapped_column(String(40))

    academic_year = relationship("AcademicYear")
    class_room = relationship("ClassRoom")
    section = relationship("Section")
    subject = relationship("Subject", back_populates="timetable_entries")
    teacher = relationship("Teacher", back_populates="timetable_entries")


class GradeRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Grade boundary rule."""

    __tablename__ = "grade_rules"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "grade_label",
            name="uq_grade_rule_year_label",
        ),
    )

    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    grade_label: Mapped[str] = mapped_column(String(20), nullable=False)
    min_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(150))
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    academic_year = relationship("AcademicYear")


class Exam(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Exam definition for a class/section/year."""

    __tablename__ = "exams"

    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("sections.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    term_label: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")

    academic_year = relationship("AcademicYear")
    class_room = relationship("ClassRoom")
    section = relationship("Section")
    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")


class ExamSubject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Subject included in an exam."""

    __tablename__ = "exam_subjects"
    __table_args__ = (
        UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),
    )

    exam_id: Mapped[str] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    pass_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    exam = relationship("Exam", back_populates="subjects")
    subject = relationship("Subject", back_populates="exam_subjects")
    marks = relationship("StudentMark", back_populates="exam_subject", cascade="all, delete-orphan")


class StudentMark(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Student mark entry for an exam subject."""

    __tablename__ = "student_marks"
    __table_args__ = (
        UniqueConstraint("exam_subject_id", "student_id", name="uq_exam_subject_student_mark"),
    )

    exam_subject_id: Mapped[str] = mapped_column(ForeignKey("exam_subjects.id"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remark: Mapped[str | None] = mapped_column(Text)

    exam_subject = relationship("ExamSubject", back_populates="marks")
    student = relationship("Student")
