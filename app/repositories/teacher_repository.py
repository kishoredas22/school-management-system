"""Teacher data access layer."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.teacher import Teacher, TeacherClassAssignment, TeacherContract, TeacherPayment


class TeacherRepository:
    """Repository for teacher persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, teacher: Teacher) -> Teacher:
        self.db.add(teacher)
        self.db.flush()
        self.db.refresh(teacher)
        return teacher

    def get_by_id(self, teacher_id: str) -> Teacher | None:
        query = (
            select(Teacher)
            .options(
                joinedload(Teacher.assignments).joinedload(TeacherClassAssignment.class_room),
                joinedload(Teacher.assignments).joinedload(TeacherClassAssignment.section),
            )
            .where(Teacher.id == teacher_id, Teacher.is_deleted.is_(False))
        )
        return self.db.execute(query).unique().scalar_one_or_none()

    def list_teachers(self) -> list[Teacher]:
        query = (
            select(Teacher)
            .options(
                joinedload(Teacher.assignments).joinedload(TeacherClassAssignment.class_room),
                joinedload(Teacher.assignments).joinedload(TeacherClassAssignment.section),
            )
            .where(Teacher.is_deleted.is_(False))
            .order_by(Teacher.name)
        )
        return self.db.execute(query).unique().scalars().all()

    def save(self, teacher: Teacher) -> Teacher:
        self.db.add(teacher)
        self.db.flush()
        self.db.refresh(teacher)
        return teacher

    def replace_assignments(self, teacher: Teacher, assignments: list[TeacherClassAssignment]) -> None:
        teacher.assignments.clear()
        teacher.assignments.extend(assignments)
        self.db.flush()

    def create_contract(self, contract: TeacherContract) -> TeacherContract:
        self.db.add(contract)
        self.db.flush()
        self.db.refresh(contract)
        return contract

    def get_contract_by_id(self, contract_id: str) -> TeacherContract | None:
        return self.db.scalar(
            select(TeacherContract)
            .options(joinedload(TeacherContract.teacher), joinedload(TeacherContract.academic_year))
            .where(TeacherContract.id == contract_id)
        )

    def get_contract_for_teacher_year(self, teacher_id: str, academic_year_id: str) -> TeacherContract | None:
        return self.db.scalar(
            select(TeacherContract).where(
                TeacherContract.teacher_id == teacher_id,
                TeacherContract.academic_year_id == academic_year_id,
            )
        )

    def list_contracts(self, teacher_id: str | None = None, academic_year_id: str | None = None) -> list[TeacherContract]:
        query = (
            select(TeacherContract)
            .options(joinedload(TeacherContract.teacher), joinedload(TeacherContract.academic_year))
            .order_by(TeacherContract.created_at.desc())
        )
        if teacher_id:
            query = query.where(TeacherContract.teacher_id == teacher_id)
        if academic_year_id:
            query = query.where(TeacherContract.academic_year_id == academic_year_id)
        return self.db.scalars(query).all()

    def list_payments(self, teacher_id: str | None = None, contract_id: str | None = None) -> list[TeacherPayment]:
        query = (
            select(TeacherPayment)
            .options(
                joinedload(TeacherPayment.teacher),
                joinedload(TeacherPayment.contract).joinedload(TeacherContract.academic_year),
            )
            .order_by(TeacherPayment.payment_date.desc(), TeacherPayment.created_at.desc())
        )
        if teacher_id:
            query = query.where(TeacherPayment.teacher_id == teacher_id)
        if contract_id:
            query = query.where(TeacherPayment.contract_id == contract_id)
        return self.db.scalars(query).all()

    def create_payment(self, payment: TeacherPayment) -> TeacherPayment:
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def get_payment_by_id(self, payment_id: str) -> TeacherPayment | None:
        return self.db.scalar(
            select(TeacherPayment)
            .options(
                joinedload(TeacherPayment.teacher),
                joinedload(TeacherPayment.contract).joinedload(TeacherContract.academic_year),
            )
            .where(TeacherPayment.id == payment_id)
        )

    def sum_payments_for_contract(
        self,
        contract_id: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Decimal:
        query = select(func.coalesce(func.sum(TeacherPayment.amount_paid), 0)).where(
            TeacherPayment.contract_id == contract_id
        )
        if start_date:
            query = query.where(TeacherPayment.payment_date >= start_date)
        if end_date:
            query = query.where(TeacherPayment.payment_date <= end_date)
        amount = self.db.scalar(query)
        return Decimal(str(amount or 0))

    def is_teacher_assigned_to_class(
        self,
        *,
        teacher_id: str,
        class_id: str,
        section_id: str | None,
        academic_year_id: str | None,
    ) -> bool:
        query = select(func.count()).select_from(TeacherClassAssignment).where(
            TeacherClassAssignment.teacher_id == teacher_id,
            TeacherClassAssignment.class_id == class_id,
        )
        if section_id:
            query = query.where(
                (TeacherClassAssignment.section_id == section_id)
                | (TeacherClassAssignment.section_id.is_(None))
            )
        else:
            query = query.where(TeacherClassAssignment.section_id.is_(None))
        if academic_year_id:
            query = query.where(
                (TeacherClassAssignment.academic_year_id == academic_year_id)
                | (TeacherClassAssignment.academic_year_id.is_(None))
            )
        return (self.db.scalar(query) or 0) > 0
