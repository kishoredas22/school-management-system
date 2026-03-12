"""Student business logic."""

from app.core.exceptions import NotFoundException, ValidationException
from app.models.enums import RoleName, StudentStatus
from app.models.student import Student, StudentAcademicRecord
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict
from app.utils.pagination import build_pagination


class StudentService:
    """Business logic for students and student status updates."""

    def __init__(
        self,
        student_repository: StudentRepository,
        reference_repository: ReferenceRepository,
        academic_year_repository: AcademicYearRepository,
    ) -> None:
        self.student_repository = student_repository
        self.reference_repository = reference_repository
        self.academic_year_repository = academic_year_repository

    def _generate_student_id(self) -> str:
        _, total = self.student_repository.list_students(
            academic_year_id=None,
            class_id=None,
            section_id=None,
            status=None,
            search=None,
            include_inactive=True,
            page=1,
            size=1,
        )
        return f"STU-{total + 1:04d}"

    def _validate_class_section(self, class_id: str, section_id: str) -> None:
        class_room = self.reference_repository.get_class(class_id)
        if not class_room:
            raise NotFoundException("Class not found")
        section = self.reference_repository.get_section_for_class(section_id, class_id)
        if not section:
            raise ValidationException("Section does not belong to the supplied class")

    def create_student(self, payload, *, actor_id: str) -> Student:
        academic_year = self.academic_year_repository.get_by_id(payload.academic_year_id)
        if not academic_year:
            raise NotFoundException("Academic year not found")
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")

        self._validate_class_section(payload.class_id, payload.section_id)

        student = Student(
            student_id=payload.student_id or self._generate_student_id(),
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            guardian_name=payload.guardian_name,
            guardian_phone=payload.guardian_phone,
            status=StudentStatus.ACTIVE,
        )
        created_student = self.student_repository.create_student(student)
        record = StudentAcademicRecord(
            student_id=created_student.id,
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            promotion_status="ADMITTED",
        )
        self.student_repository.create_academic_record(record)
        log_audit_event(
            self.student_repository.db,
            entity_name="STUDENT",
            entity_id=created_student.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created_student),
        )
        self.student_repository.db.commit()
        return created_student

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
    ):
        year_id = academic_year_id
        if not year_id:
            active_year = self.academic_year_repository.get_active()
            year_id = active_year.id if active_year else None
        rows, total = self.student_repository.list_students(
            academic_year_id=year_id,
            class_id=class_id,
            section_id=section_id,
            status=status,
            search=search,
            include_inactive=include_inactive,
            page=page,
            size=size,
        )
        data = [
            {
                "id": student.id,
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "dob": student.dob,
                "guardian_name": student.guardian_name,
                "guardian_phone": student.guardian_phone,
                "status": student.status,
                "class_id": record.class_id,
                "class_name": class_room.name,
                "section_id": record.section_id,
                "section_name": section.name,
                "academic_year_id": academic_year.id,
                "academic_year_name": academic_year.name,
                "created_at": student.created_at,
                "updated_at": student.updated_at,
            }
            for student, record, class_room, section, academic_year in rows
        ]
        return build_pagination(page, size, total, data)

    def update_student(self, student_id: str, payload, *, actor_id: str) -> Student:
        student = self.student_repository.get_by_id(student_id)
        if not student or student.is_deleted:
            raise NotFoundException("Student not found")

        old_value = model_to_dict(student)
        update_data = payload.model_dump(exclude_unset=True)
        record = None
        academic_year_id = update_data.get("academic_year_id")
        if academic_year_id:
            academic_year = self.academic_year_repository.get_by_id(academic_year_id)
            if not academic_year:
                raise NotFoundException("Academic year not found")
            if academic_year.is_closed:
                raise ValidationException("Closed academic year modification is not allowed")
            record = self.student_repository.get_record_for_year(student_id, academic_year_id)
            if not record:
                raise NotFoundException("Student academic record not found for supplied year")
        elif "class_id" in update_data or "section_id" in update_data:
            active_year = self.academic_year_repository.get_active()
            if not active_year:
                raise NotFoundException("No active academic year found")
            if active_year.is_closed:
                raise ValidationException("Closed academic year modification is not allowed")
            record = self.student_repository.get_record_for_year(student_id, active_year.id)
            if not record:
                raise NotFoundException("Student academic record not found for active year")

        if record and ("class_id" in update_data or "section_id" in update_data):
            class_id = update_data.get("class_id", record.class_id)
            section_id = update_data.get("section_id", record.section_id)
            self._validate_class_section(class_id, section_id)
            record.class_id = class_id
            record.section_id = section_id

        for field in ("student_id", "first_name", "last_name", "dob", "guardian_name", "guardian_phone"):
            if field in update_data:
                setattr(student, field, update_data[field])

        saved = self.student_repository.save_student(student)
        log_audit_event(
            self.student_repository.db,
            entity_name="STUDENT",
            entity_id=saved.id,
            action="UPDATE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.student_repository.db.commit()
        return saved

    def update_status(self, student_id: str, status: StudentStatus, *, actor_id: str, actor_role: str) -> Student:
        student = self.student_repository.get_by_id(student_id)
        if not student or student.is_deleted:
            raise NotFoundException("Student not found")

        old_value = model_to_dict(student)
        if student.status != StudentStatus.ACTIVE and actor_role != RoleName.SUPER_ADMIN:
            raise ValidationException("No reverse transition allowed without Super Admin override")

        if student.status == StudentStatus.ACTIVE and status == StudentStatus.ACTIVE:
            return student

        student.status = status
        saved = self.student_repository.save_student(student)
        log_audit_event(
            self.student_repository.db,
            entity_name="STUDENT",
            entity_id=saved.id,
            action="STATUS_CHANGE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.student_repository.db.commit()
        return saved
