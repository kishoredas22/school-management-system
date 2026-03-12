"""Reference data models for classes and sections."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClassRoom(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Class reference table."""

    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    sections = relationship("Section", back_populates="class_room", cascade="all, delete-orphan")
    student_records = relationship("StudentAcademicRecord", back_populates="class_room")
    fee_structures = relationship("FeeStructure", back_populates="class_room")
    teacher_assignments = relationship("TeacherClassAssignment", back_populates="class_room")
    teacher_subject_assignments = relationship("TeacherSubjectAssignment")
    timetable_entries = relationship("TimetableEntry")


class Section(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Section reference table."""

    __tablename__ = "sections"

    name: Mapped[str] = mapped_column(String(10), nullable=False)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)

    class_room = relationship("ClassRoom", back_populates="sections")
    student_records = relationship("StudentAcademicRecord", back_populates="section")
    teacher_assignments = relationship("TeacherClassAssignment", back_populates="section")
    teacher_subject_assignments = relationship("TeacherSubjectAssignment")
    timetable_entries = relationship("TimetableEntry")
