"""Fee data access layer."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.academic_year import AcademicYear
from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure
from app.models.reference import ClassRoom
from app.models.student import Student, StudentAcademicRecord


class FeeRepository:
    """Repository for fee structures and fee payments."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_structure(self, structure: FeeStructure) -> FeeStructure:
        self.db.add(structure)
        self.db.flush()
        self.db.refresh(structure)
        return structure

    def get_structure(self, structure_id: str) -> FeeStructure | None:
        return self.db.scalar(
            select(FeeStructure)
            .options(joinedload(FeeStructure.academic_year), joinedload(FeeStructure.class_room))
            .where(FeeStructure.id == structure_id)
        )

    def get_structures_for_class_year(self, class_id: str, academic_year_id: str) -> list[FeeStructure]:
        return self.db.scalars(
            select(FeeStructure).where(
                FeeStructure.class_id == class_id,
                FeeStructure.academic_year_id == academic_year_id,
                FeeStructure.is_active.is_(True),
            )
        ).all()

    def create_payment(self, payment: FeePayment) -> FeePayment:
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def get_payment_by_id(self, payment_id: str) -> FeePayment | None:
        return self.db.scalar(
            select(FeePayment)
            .options(
                joinedload(FeePayment.student),
                joinedload(FeePayment.fee_structure).joinedload(FeeStructure.class_room),
                joinedload(FeePayment.academic_year),
            )
            .where(FeePayment.id == payment_id)
        )

    def get_student_payment_history(self, student_id: str, academic_year_id: str) -> list[FeePayment]:
        return self.db.scalars(
            select(FeePayment)
            .where(FeePayment.student_id == student_id, FeePayment.academic_year_id == academic_year_id)
            .order_by(FeePayment.payment_date.desc(), FeePayment.created_at.desc())
        ).all()

    def get_total_paid(self, student_id: str, academic_year_id: str) -> Decimal:
        value = self.db.scalar(
            select(func.coalesce(func.sum(FeePayment.amount_paid), 0)).where(
                FeePayment.student_id == student_id,
                FeePayment.academic_year_id == academic_year_id,
            )
        )
        return Decimal(value or 0)

    def get_total_fee_for_student(self, student_id: str, academic_year_id: str) -> Decimal:
        record = self.db.scalar(
            select(StudentAcademicRecord).where(
                StudentAcademicRecord.student_id == student_id,
                StudentAcademicRecord.academic_year_id == academic_year_id,
            )
        )
        if not record:
            return Decimal("0")

        value = self.db.scalar(
            select(func.coalesce(func.sum(FeeStructure.amount), 0)).where(
                FeeStructure.class_id == record.class_id,
                FeeStructure.academic_year_id == academic_year_id,
                FeeStructure.is_active.is_(True),
            )
        )
        return Decimal(value or 0)

    def get_student_context(self, student_id: str, academic_year_id: str):
        return self.db.execute(
            select(Student, StudentAcademicRecord, ClassRoom, AcademicYear)
            .join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id)
            .join(ClassRoom, ClassRoom.id == StudentAcademicRecord.class_id)
            .join(AcademicYear, AcademicYear.id == StudentAcademicRecord.academic_year_id)
            .where(Student.id == student_id, StudentAcademicRecord.academic_year_id == academic_year_id)
        ).first()
