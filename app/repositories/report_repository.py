"""Report data access layer."""

from decimal import Decimal

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session

from app.models.attendance import StudentAttendance
from app.models.enums import StudentStatus
from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure
from app.models.reference import ClassRoom, Section
from app.models.student import Student, StudentAcademicRecord
from app.models.teacher import Teacher, TeacherContract, TeacherPayment


class ReportRepository:
    """Repository for aggregation-heavy report queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def fee_summary(self, academic_year_id: str | None = None) -> tuple[Decimal, Decimal]:
        payment_query = select(func.coalesce(func.sum(FeePayment.amount_paid), 0))
        if academic_year_id:
            payment_query = payment_query.where(FeePayment.academic_year_id == academic_year_id)
        total_collected = Decimal(self.db.scalar(payment_query) or 0)

        fee_query = (
            select(func.coalesce(func.sum(FeeStructure.amount), 0))
            .join(StudentAcademicRecord, StudentAcademicRecord.class_id == FeeStructure.class_id)
        )
        if academic_year_id:
            fee_query = fee_query.where(
                FeeStructure.academic_year_id == academic_year_id,
                StudentAcademicRecord.academic_year_id == academic_year_id,
            )
        total_fee = Decimal(self.db.scalar(fee_query) or 0)
        return total_collected, max(total_fee - total_collected, Decimal("0"))

    def fee_pending_details(self, academic_year_id: str | None = None):
        rows = self.db.execute(
            select(Student, StudentAcademicRecord, ClassRoom)
            .join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id)
            .join(ClassRoom, ClassRoom.id == StudentAcademicRecord.class_id)
            .where(Student.is_deleted.is_(False))
            .where(StudentAcademicRecord.academic_year_id == academic_year_id if academic_year_id else True)
            .order_by(Student.first_name)
        ).all()
        return rows

    def teacher_payment_summary(self, academic_year_id: str | None = None):
        contract_query = (
            select(
                TeacherContract.teacher_id.label("teacher_id"),
                func.coalesce(func.sum(TeacherContract.yearly_contract_amount), 0).label("contract_total"),
            )
            .group_by(TeacherContract.teacher_id)
        )
        payment_query = (
            select(
                TeacherPayment.teacher_id.label("teacher_id"),
                func.coalesce(func.sum(TeacherPayment.amount_paid), 0).label("total_paid"),
            )
            .join(TeacherContract, TeacherContract.id == TeacherPayment.contract_id)
            .group_by(TeacherPayment.teacher_id)
        )
        if academic_year_id:
            contract_query = contract_query.where(TeacherContract.academic_year_id == academic_year_id)
            payment_query = payment_query.where(TeacherContract.academic_year_id == academic_year_id)

        contract_subquery = contract_query.subquery()
        payment_subquery = payment_query.subquery()
        query = (
            select(
                Teacher.id,
                Teacher.name,
                func.coalesce(contract_subquery.c.contract_total, 0),
                func.coalesce(payment_subquery.c.total_paid, 0),
            )
            .outerjoin(contract_subquery, contract_subquery.c.teacher_id == Teacher.id)
            .outerjoin(payment_subquery, payment_subquery.c.teacher_id == Teacher.id)
            .where(Teacher.is_deleted.is_(False))
            .order_by(Teacher.name)
        )
        if academic_year_id:
            query = query.where(contract_subquery.c.teacher_id.is_not(None))
        return self.db.execute(query).all()

    def student_attendance_details(self, student_id: str, month: int, year: int):
        return self.db.scalars(
            select(StudentAttendance).where(
                StudentAttendance.student_id == student_id,
                func.extract("month", StudentAttendance.attendance_date) == month,
                func.extract("year", StudentAttendance.attendance_date) == year,
            )
        ).all()

    def student_status_breakdown(self, academic_year_id: str | None = None):
        query = select(Student.status, func.count(func.distinct(Student.id))).where(Student.is_deleted.is_(False))
        if academic_year_id:
            query = query.join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id).where(
                StudentAcademicRecord.academic_year_id == academic_year_id
            )
        return self.db.execute(query.group_by(Student.status)).all()

    def teacher_overview(self) -> tuple[int, int]:
        total = self.db.scalar(
            select(func.count()).select_from(Teacher).where(Teacher.is_deleted.is_(False))
        ) or 0
        active = self.db.scalar(
            select(func.count())
            .select_from(Teacher)
            .where(Teacher.is_deleted.is_(False), Teacher.is_active.is_(True))
        ) or 0
        return int(total), int(active)

    def student_overview(self, academic_year_id: str | None = None) -> tuple[int, int]:
        query = select(
            func.count(func.distinct(Student.id)),
            func.count(
                func.distinct(
                    case((Student.status == StudentStatus.ACTIVE, Student.id))
                )
            ),
        ).where(Student.is_deleted.is_(False))
        if academic_year_id:
            query = query.join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id).where(
                StudentAcademicRecord.academic_year_id == academic_year_id
            )
        total, active = self.db.execute(query).one()
        return int(total or 0), int(active or 0)

    def reference_overview(self) -> tuple[int, int]:
        class_count = self.db.scalar(select(func.count()).select_from(ClassRoom)) or 0
        section_count = self.db.scalar(select(func.count()).select_from(Section)) or 0
        return int(class_count), int(section_count)

    def monthly_fee_collection(self, *, calendar_year: int, academic_year_id: str | None = None):
        query = select(
            extract("month", FeePayment.payment_date).label("month"),
            func.coalesce(func.sum(FeePayment.amount_paid), 0).label("amount"),
        ).where(extract("year", FeePayment.payment_date) == calendar_year)
        if academic_year_id:
            query = query.where(FeePayment.academic_year_id == academic_year_id)
        return self.db.execute(query.group_by("month").order_by("month")).all()

    def monthly_teacher_payout(self, *, calendar_year: int, academic_year_id: str | None = None):
        query = (
            select(
                extract("month", TeacherPayment.payment_date).label("month"),
                func.coalesce(func.sum(TeacherPayment.amount_paid), 0).label("amount"),
            )
            .join(TeacherContract, TeacherContract.id == TeacherPayment.contract_id)
            .where(extract("year", TeacherPayment.payment_date) == calendar_year)
        )
        if academic_year_id:
            query = query.where(TeacherContract.academic_year_id == academic_year_id)
        return self.db.execute(query.group_by("month").order_by("month")).all()
