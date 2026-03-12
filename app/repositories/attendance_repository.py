"""Attendance data access layer."""

from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import StudentAttendance, TeacherAttendance
from app.models.enums import AttendanceStatus


class AttendanceRepository:
    """Repository for attendance persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_student_attendance(self, student_id: str, academic_year_id: str, attendance_date: date) -> StudentAttendance | None:
        return self.db.scalar(
            select(StudentAttendance).where(
                StudentAttendance.student_id == student_id,
                StudentAttendance.academic_year_id == academic_year_id,
                StudentAttendance.attendance_date == attendance_date,
            )
        )

    def save_student_attendance(self, record: StudentAttendance) -> StudentAttendance:
        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)
        return record

    def list_student_attendance_for_date(
        self,
        *,
        academic_year_id: str,
        attendance_date: date,
        student_ids: list[str],
    ) -> list[StudentAttendance]:
        if not student_ids:
            return []
        return self.db.scalars(
            select(StudentAttendance).where(
                StudentAttendance.academic_year_id == academic_year_id,
                StudentAttendance.attendance_date == attendance_date,
                StudentAttendance.student_id.in_(student_ids),
            )
        ).all()

    def get_teacher_attendance(self, teacher_id: str, academic_year_id: str, attendance_date: date) -> TeacherAttendance | None:
        return self.db.scalar(
            select(TeacherAttendance).where(
                TeacherAttendance.teacher_id == teacher_id,
                TeacherAttendance.academic_year_id == academic_year_id,
                TeacherAttendance.attendance_date == attendance_date,
            )
        )

    def save_teacher_attendance(self, record: TeacherAttendance) -> TeacherAttendance:
        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)
        return record

    def list_teacher_attendance_for_date(
        self,
        *,
        academic_year_id: str,
        attendance_date: date,
    ) -> list[TeacherAttendance]:
        return self.db.scalars(
            select(TeacherAttendance)
            .options(joinedload(TeacherAttendance.teacher))
            .where(
                TeacherAttendance.academic_year_id == academic_year_id,
                TeacherAttendance.attendance_date == attendance_date,
            )
            .order_by(TeacherAttendance.created_at.desc())
        ).all()

    def get_student_attendance_rows(self, *, month: int, year: int, academic_year_id: str | None = None):
        query = select(StudentAttendance).where(
            extract("month", StudentAttendance.attendance_date) == month,
            extract("year", StudentAttendance.attendance_date) == year,
        )
        if academic_year_id:
            query = query.where(StudentAttendance.academic_year_id == academic_year_id)
        return self.db.scalars(query).all()

    def get_teacher_attendance_rows(
        self,
        *,
        month: int,
        year: int,
        academic_year_id: str | None = None,
        teacher_id: str | None = None,
    ):
        query = select(TeacherAttendance).where(
            extract("month", TeacherAttendance.attendance_date) == month,
            extract("year", TeacherAttendance.attendance_date) == year,
        )
        if academic_year_id:
            query = query.where(TeacherAttendance.academic_year_id == academic_year_id)
        if teacher_id:
            query = query.where(TeacherAttendance.teacher_id == teacher_id)
        return self.db.scalars(query).all()

    def count_teacher_present_days(
        self,
        *,
        teacher_id: str,
        academic_year_id: str,
        start_date: date,
        end_date: date,
    ) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(TeacherAttendance)
                .where(
                    TeacherAttendance.teacher_id == teacher_id,
                    TeacherAttendance.academic_year_id == academic_year_id,
                    TeacherAttendance.attendance_date >= start_date,
                    TeacherAttendance.attendance_date <= end_date,
                    TeacherAttendance.status == AttendanceStatus.PRESENT,
                )
            )
            or 0
        )
