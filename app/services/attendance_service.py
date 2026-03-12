"""Attendance business logic."""

from datetime import date

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.attendance import StudentAttendance, TeacherAttendance
from app.models.enums import RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict, utcnow


class AttendanceService:
    """Business logic for attendance operations."""

    def __init__(
        self,
        attendance_repository: AttendanceRepository,
        academic_year_repository: AcademicYearRepository,
        student_repository: StudentRepository,
        teacher_repository: TeacherRepository,
    ) -> None:
        self.attendance_repository = attendance_repository
        self.academic_year_repository = academic_year_repository
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository

    def _get_active_open_year(self):
        academic_year = self.academic_year_repository.get_active()
        if not academic_year:
            raise NotFoundException("No active academic year found")
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        return academic_year

    def _enforce_edit_window(self, attendance_date: date) -> None:
        if attendance_date > utcnow().date():
            raise ValidationException("Future attendance is not allowed")
        delta_days = (utcnow().date() - attendance_date).days
        if delta_days > settings.attendance_edit_window_days:
            raise ValidationException("Attendance edit after window is not allowed")

    def mark_student_attendance(self, payload, *, current_user) -> list[StudentAttendance]:
        academic_year = self._get_active_open_year()
        self._enforce_edit_window(payload.date)
        if current_user.role.name == RoleName.TEACHER:
            if not current_user.teacher_id:
                raise ValidationException("Teacher account is not linked to a teacher profile")
            if not self.teacher_repository.is_teacher_assigned_to_class(
                teacher_id=current_user.teacher_id,
                class_id=payload.class_id,
                section_id=payload.section_id,
                academic_year_id=academic_year.id,
            ):
                raise ValidationException("Teacher can see only assigned classes")

        saved_records: list[StudentAttendance] = []
        for item in payload.attendance:
            student = self.student_repository.get_by_id(item.student_id)
            if not student or student.is_deleted:
                raise NotFoundException("Student not found")
            record = self.student_repository.get_record_for_year(item.student_id, academic_year.id)
            if not record or record.class_id != payload.class_id or record.section_id != payload.section_id:
                raise ValidationException("Student does not belong to supplied class/section")

            existing = self.attendance_repository.get_student_attendance(item.student_id, academic_year.id, payload.date)
            if existing:
                existing.status = item.status
                saved = self.attendance_repository.save_student_attendance(existing)
            else:
                saved = self.attendance_repository.save_student_attendance(
                    StudentAttendance(
                        student_id=item.student_id,
                        academic_year_id=academic_year.id,
                        attendance_date=payload.date,
                        status=item.status,
                        marked_by=current_user.id,
                    )
                )
            saved_records.append(saved)
            log_audit_event(
                self.attendance_repository.db,
                entity_name="STUDENT_ATTENDANCE",
                entity_id=saved.id,
                action="UPSERT",
                performed_by=current_user.id,
                new_value=model_to_dict(saved),
            )

        self.attendance_repository.db.commit()
        return saved_records

    def get_student_register(
        self,
        *,
        class_id: str,
        section_id: str,
        attendance_date: date,
        current_user,
        search: str | None = None,
    ) -> list[dict]:
        academic_year = self._get_active_open_year()
        self._enforce_edit_window(attendance_date)
        if current_user.role.name == RoleName.TEACHER:
            if not current_user.teacher_id:
                raise ValidationException("Teacher account is not linked to a teacher profile")
            if not self.teacher_repository.is_teacher_assigned_to_class(
                teacher_id=current_user.teacher_id,
                class_id=class_id,
                section_id=section_id,
                academic_year_id=academic_year.id,
            ):
                raise ValidationException("Teacher can see only assigned classes")

        rows = self.student_repository.list_students_for_section(
            academic_year_id=academic_year.id,
            class_id=class_id,
            section_id=section_id,
            search=search,
        )
        student_ids = [student.id for student, *_ in rows]
        existing = self.attendance_repository.list_student_attendance_for_date(
            academic_year_id=academic_year.id,
            attendance_date=attendance_date,
            student_ids=student_ids,
        )
        existing_map = {item.student_id: item for item in existing}
        return [
            {
                "student_id": student.id,
                "student_code": student.student_id,
                "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
                "status": existing_map.get(student.id).status if student.id in existing_map else None,
            }
            for student, *_ in rows
        ]

    def mark_teacher_attendance(self, payload, *, actor_id: str) -> TeacherAttendance:
        academic_year = self._get_active_open_year()
        self._enforce_edit_window(payload.date)
        teacher = self.teacher_repository.get_by_id(payload.teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")

        existing = self.attendance_repository.get_teacher_attendance(payload.teacher_id, academic_year.id, payload.date)
        if existing:
            existing.status = payload.status
            existing.note = payload.note
            saved = self.attendance_repository.save_teacher_attendance(existing)
        else:
            saved = self.attendance_repository.save_teacher_attendance(
                TeacherAttendance(
                    teacher_id=payload.teacher_id,
                    academic_year_id=academic_year.id,
                    attendance_date=payload.date,
                    status=payload.status,
                    note=payload.note,
                )
            )

        log_audit_event(
            self.attendance_repository.db,
            entity_name="TEACHER_ATTENDANCE",
            entity_id=saved.id,
            action="UPSERT",
            performed_by=actor_id,
            new_value=model_to_dict(saved),
        )
        self.attendance_repository.db.commit()
        return saved

    def list_teacher_attendance(self, *, attendance_date: date) -> list[dict]:
        academic_year = self._get_active_open_year()
        self._enforce_edit_window(attendance_date)
        rows = self.attendance_repository.list_teacher_attendance_for_date(
            academic_year_id=academic_year.id,
            attendance_date=attendance_date,
        )
        return [
            {
                "id": row.id,
                "teacher_id": row.teacher_id,
                "teacher_name": row.teacher.name,
                "attendance_date": row.attendance_date,
                "status": row.status,
                "note": row.note,
            }
            for row in rows
        ]
