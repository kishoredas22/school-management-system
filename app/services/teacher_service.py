"""Teacher business logic."""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.teacher import Teacher, TeacherClassAssignment, TeacherContract, TeacherPayment
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.teacher_repository import TeacherRepository
from app.utils.audit_logger import log_audit_event
from app.utils.email_sender import send_email_with_attachment
from app.utils.helpers import generate_receipt_number, model_to_dict
from app.utils.receipt_generator import generate_salary_slip


class TeacherService:
    """Business logic for teacher profile and salary management."""

    def __init__(
        self,
        teacher_repository: TeacherRepository,
        reference_repository: ReferenceRepository,
        academic_year_repository: AcademicYearRepository,
        attendance_repository: AttendanceRepository,
    ) -> None:
        self.teacher_repository = teacher_repository
        self.reference_repository = reference_repository
        self.academic_year_repository = academic_year_repository
        self.attendance_repository = attendance_repository

    def _build_assignments(self, payload_assignments: list) -> list[TeacherClassAssignment]:
        assignments: list[TeacherClassAssignment] = []
        for item in payload_assignments:
            class_room = self.reference_repository.get_class(item.class_id)
            if not class_room:
                raise NotFoundException("Class not found")
            if item.section_id and not self.reference_repository.get_section_for_class(item.section_id, item.class_id):
                raise ValidationException("Section does not belong to the supplied class")
            if item.academic_year_id:
                year = self.academic_year_repository.get_by_id(item.academic_year_id)
                if not year:
                    raise NotFoundException("Academic year not found")
            assignments.append(
                TeacherClassAssignment(
                    class_id=item.class_id,
                    section_id=item.section_id,
                    academic_year_id=item.academic_year_id,
                )
            )
        return assignments

    def create_teacher(self, payload, *, actor_id: str) -> Teacher:
        teacher = Teacher(name=payload.name, phone=payload.phone, email=payload.email, is_active=True)
        teacher.assignments = self._build_assignments(payload.assigned_classes)
        created = self.teacher_repository.create(teacher)
        log_audit_event(
            self.teacher_repository.db,
            entity_name="TEACHER",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.teacher_repository.db.commit()
        return created

    def update_teacher(self, teacher_id: str, payload, *, actor_id: str) -> Teacher:
        teacher = self.teacher_repository.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")

        old_value = model_to_dict(teacher)
        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data:
            teacher.name = update_data["name"]
        if "phone" in update_data:
            teacher.phone = update_data["phone"]
        if "email" in update_data:
            teacher.email = update_data["email"]
        if "is_active" in update_data:
            teacher.is_active = update_data["is_active"]
        if payload.assigned_classes is not None:
            assignments = self._build_assignments(payload.assigned_classes)
            self.teacher_repository.replace_assignments(teacher, assignments)

        saved = self.teacher_repository.save(teacher)
        log_audit_event(
            self.teacher_repository.db,
            entity_name="TEACHER",
            entity_id=saved.id,
            action="UPDATE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.teacher_repository.db.commit()
        return saved

    def list_teachers(self) -> list[Teacher]:
        return self.teacher_repository.list_teachers()

    def get_teacher_detail(self, teacher_id: str) -> dict:
        teacher = self.teacher_repository.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")

        contracts = self.teacher_repository.list_contracts(teacher_id=teacher_id)
        payments = self.teacher_repository.list_payments(teacher_id=teacher_id)

        payment_items = []
        for payment in payments:
            contract_total = payment.contract.yearly_contract_amount
            total_paid = self.teacher_repository.sum_payments_for_contract(payment.contract_id)
            pending_balance = max(contract_total - total_paid, Decimal("0"))
            payment_items.append(
                {
                    "id": payment.id,
                    "receipt_number": payment.receipt_number,
                    "payment_date": payment.payment_date.isoformat(),
                    "amount_paid": str(payment.amount_paid),
                    "payment_mode": payment.payment_mode.value,
                    "contract_id": payment.contract_id,
                    "academic_year_name": payment.contract.academic_year.name,
                    "contract_total": str(contract_total),
                    "pending_balance": str(pending_balance),
                }
            )

        return {
            "id": teacher.id,
            "name": teacher.name,
            "phone": teacher.phone,
            "email": teacher.email,
            "is_active": teacher.is_active,
            "created_at": teacher.created_at.isoformat(),
            "assignment_count": len(teacher.assignments),
            "assignments": [
                {
                    "id": assignment.id,
                    "class_id": assignment.class_id,
                    "class_name": assignment.class_room.name if assignment.class_room else None,
                    "section_id": assignment.section_id,
                    "section_name": assignment.section.name if assignment.section else None,
                    "academic_year_id": assignment.academic_year_id,
                }
                for assignment in teacher.assignments
            ],
            "contracts": [
                {
                    "id": item.id,
                    "teacher_id": item.teacher_id,
                    "teacher_name": teacher.name,
                    "academic_year_id": item.academic_year_id,
                    "academic_year_name": item.academic_year.name,
                    "yearly_contract_amount": str(item.yearly_contract_amount),
                    "monthly_salary": str(item.monthly_salary or Decimal("0")),
                    "created_at": item.created_at.isoformat(),
                }
                for item in contracts
            ],
            "payments": payment_items,
        }

    def create_contract(self, payload, *, actor_id: str) -> TeacherContract:
        teacher = self.teacher_repository.get_by_id(payload.teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")
        academic_year = self.academic_year_repository.get_by_id(payload.academic_year_id)
        if not academic_year:
            raise NotFoundException("Academic year not found")
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        existing_contract = self.teacher_repository.get_contract_for_teacher_year(payload.teacher_id, payload.academic_year_id)
        if existing_contract:
            raise ConflictException("Teacher contract already exists for academic year")

        monthly_salary = payload.monthly_salary
        if monthly_salary is None:
            monthly_salary = (payload.yearly_contract_amount / Decimal("12")).quantize(Decimal("0.01"))

        contract = TeacherContract(
            teacher_id=payload.teacher_id,
            academic_year_id=payload.academic_year_id,
            yearly_contract_amount=payload.yearly_contract_amount,
            monthly_salary=monthly_salary,
        )
        created = self.teacher_repository.create_contract(contract)
        log_audit_event(
            self.teacher_repository.db,
            entity_name="TEACHER_CONTRACT",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.teacher_repository.db.commit()
        return created

    def record_payment(self, payload, *, actor_id: str) -> TeacherPayment:
        teacher = self.teacher_repository.get_by_id(payload.teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")
        contract = self.teacher_repository.get_contract_by_id(payload.contract_id)
        if not contract:
            raise NotFoundException("Teacher contract not found")
        if contract.teacher_id != payload.teacher_id:
            raise ValidationException("Contract does not belong to supplied teacher")
        if contract.academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")

        payment = TeacherPayment(
            teacher_id=payload.teacher_id,
            contract_id=payload.contract_id,
            amount_paid=payload.amount,
            payment_mode=payload.payment_mode,
            payment_date=payload.payment_date,
            receipt_number=generate_receipt_number("SAL"),
        )
        created = self.teacher_repository.create_payment(payment)
        log_audit_event(
            self.teacher_repository.db,
            entity_name="TEACHER_PAYMENT",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.teacher_repository.db.commit()
        return created

    def build_salary_slip_payload(self, payment_id: str) -> dict:
        payment = self.teacher_repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundException("Teacher payment not found")

        payment_month_start = payment.payment_date.replace(day=1)
        payment_month_end = date(
            payment.payment_date.year,
            payment.payment_date.month,
            monthrange(payment.payment_date.year, payment.payment_date.month)[1],
        )
        academic_year_start = payment.contract.academic_year.start_date
        days_worked = self.attendance_repository.count_teacher_present_days(
            teacher_id=payment.teacher_id,
            academic_year_id=payment.contract.academic_year_id,
            start_date=payment_month_start,
            end_date=payment_month_end,
        )
        paid_for_month = self.teacher_repository.sum_payments_for_contract(
            payment.contract_id,
            start_date=payment_month_start,
            end_date=payment_month_end,
        )
        paid_year_to_date = self.teacher_repository.sum_payments_for_contract(
            payment.contract_id,
            start_date=academic_year_start,
            end_date=payment.payment_date,
        )
        total_paid = self.teacher_repository.sum_payments_for_contract(payment.contract_id)
        remaining_balance = max(payment.contract.yearly_contract_amount - total_paid, Decimal("0"))
        return {
            "receipt_number": payment.receipt_number,
            "teacher_name": payment.teacher.name,
            "teacher_phone": payment.teacher.phone or "",
            "academic_year": payment.contract.academic_year.name,
            "salary_month": payment.payment_date.strftime("%B %Y"),
            "payment_date": payment.payment_date.isoformat(),
            "paid_amount": str(payment.amount_paid),
            "paid_for_month": str(paid_for_month),
            "paid_year_to_date": str(paid_year_to_date),
            "remaining_balance": str(remaining_balance),
            "monthly_salary": str(payment.contract.monthly_salary or Decimal("0")),
            "contract_total": str(payment.contract.yearly_contract_amount),
            "days_worked": days_worked,
            "total_days_in_month": payment_month_end.day,
            "payment_mode": payment.payment_mode.value,
        }

    def prepare_salary_slip_share(self, payment_id: str, *, channel: str) -> dict:
        payment = self.teacher_repository.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundException("Teacher payment not found")

        payload = self.build_salary_slip_payload(payment_id)
        teacher = payment.teacher
        if channel == "EMAIL":
            if not teacher.email:
                raise ValidationException("Teacher email is not available for this profile")
            slip_pdf = generate_salary_slip(payload)
            subject = f"Salary slip {payload['salary_month']} - {payload['receipt_number']}"
            body = (
                f"Dear {teacher.name},\n\n"
                f"Please find attached your salary slip for {payload['salary_month']}.\n"
                f"Receipt number: {payload['receipt_number']}\n"
                f"Amount paid: {payload['paid_amount']}\n\n"
                "Regards,\n"
                "Vivekananda Siksha Kendra (VSK)"
            )
            send_email_with_attachment(
                to_email=teacher.email,
                subject=subject,
                body_text=body,
                attachment_bytes=slip_pdf,
                attachment_filename=f"{payload['receipt_number']}.pdf",
            )
            destination = teacher.email
            launch_url = None
            delivery = "SMTP_SENT"
        elif channel == "WHATSAPP":
            raise ValidationException(
                "WhatsApp PDF delivery requires a configured business sender/provider, so it is not enabled yet."
            )
        else:
            raise ValidationException("Unsupported sharing channel")

        return {
            "channel": channel,
            "destination": destination,
            "launch_url": launch_url,
            "receipt_number": payload["receipt_number"],
            "salary_month": payload["salary_month"],
            "delivery": delivery,
            "sender_email": settings.smtp_sender_email if channel == "EMAIL" else None,
        }
