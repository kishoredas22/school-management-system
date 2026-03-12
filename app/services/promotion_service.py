"""Promotion business logic."""

import re

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.enums import PromotionAction, StudentStatus
from app.models.student import StudentAcademicRecord
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.utils.audit_logger import log_audit_event


class PromotionService:
    """Year-end promotion workflows."""

    def __init__(
        self,
        student_repository: StudentRepository,
        academic_year_repository: AcademicYearRepository,
        reference_repository: ReferenceRepository | None = None,
    ) -> None:
        self.student_repository = student_repository
        self.academic_year_repository = academic_year_repository
        self.reference_repository = reference_repository

    def _resolve_next_class_id(self, class_id: str) -> str:
        if not self.reference_repository:
            return class_id
        current_class = self.reference_repository.get_class(class_id)
        if not current_class:
            return class_id
        match = re.search(r"(\d+)$", current_class.name.strip())
        if not match:
            return class_id
        next_name = re.sub(r"(\d+)$", lambda item: str(int(item.group(1)) + 1), current_class.name.strip())
        next_class = self.reference_repository.get_class_by_name(next_name)
        return next_class.id if next_class else class_id

    def promote_students(self, payload, *, actor_id: str) -> dict:
        source_year = self.academic_year_repository.get_by_id(payload.academic_year_from)
        target_year = self.academic_year_repository.get_by_id(payload.academic_year_to)
        if not source_year or not target_year:
            raise NotFoundException("Academic year not found")
        if source_year.is_closed or target_year.is_closed:
            raise ValidationException("Cannot promote if year closed")

        rows = self.student_repository.list_records_for_promotion(
            academic_year_id=payload.academic_year_from,
            student_ids=payload.student_ids or None,
        )
        if not rows:
            raise NotFoundException("No students found for promotion")

        processed_ids: list[str] = []
        for student, current_record in rows:
            if student.status != StudentStatus.ACTIVE and payload.action != PromotionAction.PASS_OUT:
                continue

            current_record.promotion_status = payload.action.value

            if payload.action in {PromotionAction.PROMOTE, PromotionAction.HOLD}:
                existing_target = self.student_repository.get_record_for_year(student.id, payload.academic_year_to)
                if existing_target:
                    raise ConflictException("Student already has a record in the target academic year")
                new_record = StudentAcademicRecord(
                    student_id=student.id,
                    academic_year_id=payload.academic_year_to,
                    class_id=current_record.class_id,
                    section_id=current_record.section_id,
                    promotion_status=payload.action.value,
                )
                self.student_repository.create_academic_record(new_record)
            elif payload.action == PromotionAction.PASS_OUT:
                student.status = StudentStatus.PASSED_OUT
                self.student_repository.save_student(student)

            processed_ids.append(student.id)
            log_audit_event(
                self.student_repository.db,
                entity_name="STUDENT",
                entity_id=student.id,
                action=f"PROMOTION_{payload.action.value}",
                performed_by=actor_id,
                new_value={"from_year": payload.academic_year_from, "to_year": payload.academic_year_to},
            )

        self.student_repository.db.commit()
        return {
            "processed_count": len(processed_ids),
            "action": payload.action,
            "student_ids": processed_ids,
        }

    def promote_students_advanced(self, payload, *, actor_id: str) -> dict:
        source_year = self.academic_year_repository.get_by_id(payload.academic_year_from)
        target_year = self.academic_year_repository.get_by_id(payload.academic_year_to)
        if not source_year or not target_year:
            raise NotFoundException("Academic year not found")
        if source_year.is_closed or target_year.is_closed:
            raise ValidationException("Cannot promote if year closed")

        decision_map = {str(item.student_id): item for item in payload.decisions}
        target_ids = [str(item.student_id) for item in payload.decisions] or [str(item) for item in payload.student_ids]
        rows = self.student_repository.list_records_for_promotion(
            academic_year_id=payload.academic_year_from,
            student_ids=target_ids or None,
        )
        if not rows:
            raise NotFoundException("No students found for promotion")

        processed: list[dict] = []
        for student, current_record in rows:
            decision = decision_map.get(str(student.id))
            action = decision.action if decision else payload.default_action
            if student.status != StudentStatus.ACTIVE and action != PromotionAction.PASS_OUT:
                continue

            current_record.promotion_status = action.value

            target_class_id = decision.target_class_id if decision and decision.target_class_id else payload.default_target_class_id
            target_section_id = decision.target_section_id if decision and decision.target_section_id else payload.default_target_section_id

            if action == PromotionAction.PROMOTE:
                target_class_id = target_class_id or self._resolve_next_class_id(current_record.class_id)
                target_section_id = target_section_id or current_record.section_id
            elif action == PromotionAction.HOLD:
                target_class_id = target_class_id or current_record.class_id
                target_section_id = target_section_id or current_record.section_id

            if action in {PromotionAction.PROMOTE, PromotionAction.HOLD}:
                existing_target = self.student_repository.get_record_for_year(student.id, payload.academic_year_to)
                if existing_target:
                    raise ConflictException("Student already has a record in the target academic year")
                new_record = StudentAcademicRecord(
                    student_id=student.id,
                    academic_year_id=payload.academic_year_to,
                    class_id=target_class_id,
                    section_id=target_section_id,
                    promotion_status=action.value,
                )
                self.student_repository.create_academic_record(new_record)
            elif action == PromotionAction.PASS_OUT:
                student.status = StudentStatus.PASSED_OUT
                self.student_repository.save_student(student)

            processed.append(
                {
                    "student_id": student.id,
                    "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
                    "action": action.value,
                    "target_class_id": target_class_id,
                    "target_section_id": target_section_id,
                    "remark": decision.remark if decision else None,
                }
            )
            log_audit_event(
                self.student_repository.db,
                entity_name="STUDENT",
                entity_id=student.id,
                action=f"PROMOTION_{action.value}",
                performed_by=actor_id,
                new_value={
                    "from_year": payload.academic_year_from,
                    "to_year": payload.academic_year_to,
                    "target_class_id": target_class_id,
                    "target_section_id": target_section_id,
                },
            )

        self.student_repository.db.commit()
        return {
            "processed_count": len(processed),
            "action": payload.default_action,
            "student_ids": [item["student_id"] for item in processed],
            "decisions": processed,
        }
