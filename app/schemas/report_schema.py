"""Reporting schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class FeeReportSummary(BaseModel):
    """Fee summary report payload."""

    total_collected: Decimal
    total_pending: Decimal


class PendingFeeItem(BaseModel):
    """Drill-down fee pending row."""

    student_id: UUID
    student_name: str
    class_name: str | None
    total_fee: Decimal
    total_paid: Decimal
    pending: Decimal


class ClassFeeBalanceItem(BaseModel):
    """Class-level pending fee aggregation."""

    class_name: str
    student_count: int
    pending_total: Decimal
    collected_total: Decimal


class TeacherPaymentReportItem(BaseModel):
    """Teacher salary report row."""

    teacher_id: UUID
    teacher_name: str
    contract_total: Decimal
    total_paid: Decimal
    pending_balance: Decimal


class AttendanceDetailItem(BaseModel):
    """Attendance detail row."""

    attendance_date: date
    status: str


class StudentStatusReportItem(BaseModel):
    """Student status breakdown row."""

    status: str
    count: int


class MonthlyFinanceTrendItem(BaseModel):
    """Monthly fee and payroll trend row."""

    month: int
    label: str
    fee_collected: Decimal
    teacher_paid: Decimal
    net_cashflow: Decimal


class DashboardOverview(BaseModel):
    """Operational dashboard summary payload."""

    student_total: int
    active_students: int
    teacher_total: int
    active_teachers: int
    class_count: int
    section_count: int
    fee_collected: Decimal
    fee_pending: Decimal
    pending_students: int
    salary_pending: Decimal
    student_status: list[StudentStatusReportItem]
