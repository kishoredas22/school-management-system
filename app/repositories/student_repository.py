"""Student data access layer."""

from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.academic_year import AcademicYear
from app.models.reference import ClassRoom, Section
from app.models.student import Student, StudentAcademicRecord


class StudentRepository:
    """Repository for student persistence and query composition."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_student(self, student: Student) -> Student:
        self.db.add(student)
        self.db.flush()
        self.db.refresh(student)
        return student

    def create_academic_record(self, record: StudentAcademicRecord) -> StudentAcademicRecord:
        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)
        return record

    def get_by_id(self, student_id: str) -> Student | None:
        return self.db.scalar(
            select(Student).options(joinedload(Student.academic_records)).where(Student.id == student_id)
        )

    def get_record_for_year(self, student_id: str, academic_year_id: str) -> StudentAcademicRecord | None:
        return self.db.scalar(
            select(StudentAcademicRecord).where(
                StudentAcademicRecord.student_id == student_id,
                StudentAcademicRecord.academic_year_id == academic_year_id,
            )
        )

    def list_students(
        self,
        *,
        academic_year_id: str | None,
        class_id: str | None,
        section_id: str | None,
        status: str | None,
        search: str | None,
        include_inactive: bool,
        page: int,
        size: int,
    ) -> tuple[Sequence[tuple[Student, StudentAcademicRecord, ClassRoom, Section, AcademicYear]], int]:
        query: Select = (
            select(Student, StudentAcademicRecord, ClassRoom, Section, AcademicYear)
            .join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id)
            .join(ClassRoom, ClassRoom.id == StudentAcademicRecord.class_id)
            .join(Section, Section.id == StudentAcademicRecord.section_id)
            .join(AcademicYear, AcademicYear.id == StudentAcademicRecord.academic_year_id)
            .where(Student.is_deleted.is_(False))
        )
        if academic_year_id:
            query = query.where(StudentAcademicRecord.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(StudentAcademicRecord.class_id == class_id)
        if section_id:
            query = query.where(StudentAcademicRecord.section_id == section_id)
        if status:
            query = query.where(Student.status == status)
        elif not include_inactive:
            query = query.where(Student.status == "ACTIVE")
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Student.first_name.ilike(term),
                    Student.last_name.ilike(term),
                    Student.student_id.ilike(term),
                )
            )

        ordered_query = query.order_by(Student.first_name, Student.last_name)
        total = self.db.scalar(select(func.count()).select_from(ordered_query.subquery())) or 0
        rows = self.db.execute(ordered_query.offset((page - 1) * size).limit(size)).all()
        return rows, total

    def list_students_for_section(
        self,
        *,
        academic_year_id: str,
        class_id: str,
        section_id: str,
        search: str | None = None,
    ) -> Sequence[tuple[Student, StudentAcademicRecord, ClassRoom, Section, AcademicYear]]:
        rows, _ = self.list_students(
            academic_year_id=academic_year_id,
            class_id=class_id,
            section_id=section_id,
            status="ACTIVE",
            search=search,
            include_inactive=False,
            page=1,
            size=1000,
        )
        return rows

    def save_student(self, student: Student) -> Student:
        self.db.add(student)
        self.db.flush()
        self.db.refresh(student)
        return student

    def list_records_for_promotion(
        self,
        *,
        academic_year_id: str,
        student_ids: list[str] | None = None,
    ) -> list[tuple[Student, StudentAcademicRecord]]:
        query = (
            select(Student, StudentAcademicRecord)
            .join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id)
            .where(
                Student.is_deleted.is_(False),
                StudentAcademicRecord.academic_year_id == academic_year_id,
            )
        )
        if student_ids:
            query = query.where(Student.id.in_(student_ids))
        return self.db.execute(query.order_by(Student.first_name)).all()
