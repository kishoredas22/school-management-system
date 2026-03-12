"""Fee business logic."""

from decimal import Decimal

from app.core.exceptions import NotFoundException, ValidationException
from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.fee_repository import FeeRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import generate_receipt_number, model_to_dict


class FeeService:
    """Business logic for fee structures, payments, and receipts."""

    def __init__(
        self,
        fee_repository: FeeRepository,
        student_repository: StudentRepository,
        academic_year_repository: AcademicYearRepository,
        reference_repository: ReferenceRepository,
    ) -> None:
        self.fee_repository = fee_repository
        self.student_repository = student_repository
        self.academic_year_repository = academic_year_repository
        self.reference_repository = reference_repository

    def create_fee_structure(self, payload, *, actor_id: str) -> FeeStructure:
        academic_year = self.academic_year_repository.get_by_id(payload.academic_year_id)
        if not academic_year:
            raise NotFoundException("Academic year not found")
        if academic_year.is_closed:
            raise ValidationException("Cannot modify after year closure")
        if not self.reference_repository.get_class(payload.class_id):
            raise NotFoundException("Class not found")

        structure = FeeStructure(
            class_id=payload.class_id,
            academic_year_id=payload.academic_year_id,
            fee_name=payload.fee_name,
            amount=payload.amount,
            fee_type=payload.fee_type,
            is_active=True,
        )
        created = self.fee_repository.create_structure(structure)
        log_audit_event(
            self.fee_repository.db,
            entity_name="FEE_STRUCTURE",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.fee_repository.db.commit()
        return created

    def record_payment(self, payload, *, actor_id: str) -> FeePayment:
        student = self.student_repository.get_by_id(payload.student_id)
        if not student or student.is_deleted:
            raise NotFoundException("Student not found")
        structure = self.fee_repository.get_structure(payload.fee_structure_id)
        if not structure:
            raise NotFoundException("Fee structure not found")
        if structure.academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")

        payment = FeePayment(
            student_id=payload.student_id,
            academic_year_id=structure.academic_year_id,
            fee_structure_id=payload.fee_structure_id,
            amount_paid=payload.amount,
            payment_mode=payload.payment_mode,
            payment_date=payload.payment_date,
            receipt_number=generate_receipt_number("FEE"),
        )
        created = self.fee_repository.create_payment(payment)
        log_audit_event(
            self.fee_repository.db,
            entity_name="FEE_PAYMENT",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.fee_repository.db.commit()
        return created

    def get_student_fee_summary(self, student_id: str, academic_year_id: str | None = None) -> dict:
        student = self.student_repository.get_by_id(student_id)
        if not student or student.is_deleted:
            raise NotFoundException("Student not found")

        year_id = academic_year_id
        if not year_id:
            active_year = self.academic_year_repository.get_active()
            if not active_year:
                raise NotFoundException("No active academic year found")
            year_id = active_year.id

        total_fee = self.fee_repository.get_total_fee_for_student(student_id, year_id)
        total_paid = self.fee_repository.get_total_paid(student_id, year_id)
        history = self.fee_repository.get_student_payment_history(student_id, year_id)
        return {
            "total_fee": total_fee,
            "total_paid": total_paid,
            "pending": max(total_fee - total_paid, Decimal("0")),
            "payment_history": history,
        }

    def build_fee_receipt_payload(self, payment_id: str) -> dict:
        payment = self.fee_repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundException("Fee payment not found")

        total_fee = self.fee_repository.get_total_fee_for_student(payment.student_id, payment.academic_year_id)
        total_paid = self.fee_repository.get_total_paid(payment.student_id, payment.academic_year_id)
        pending_balance = max(total_fee - total_paid, Decimal("0"))
        context = self.fee_repository.get_student_context(payment.student_id, payment.academic_year_id)
        if not context:
            raise NotFoundException("Student academic context not found")
        student, _, class_room, academic_year = context
        return {
            "receipt_number": payment.receipt_number,
            "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
            "student_id": student.student_id or "",
            "academic_year": academic_year.name,
            "class_name": class_room.name,
            "paid_amount": str(payment.amount_paid),
            "pending_balance": str(pending_balance),
            "payment_mode": payment.payment_mode.value,
        }
