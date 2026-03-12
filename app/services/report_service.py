"""Reporting business logic."""

from calendar import month_abbr
from collections import defaultdict
from decimal import Decimal

from app.core.exceptions import NotFoundException
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.fee_repository import FeeRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.student_repository import StudentRepository


class ReportService:
    """Business logic for summary, drill-down, and export-friendly reports."""

    def __init__(
        self,
        report_repository: ReportRepository,
        fee_repository: FeeRepository,
        attendance_repository: AttendanceRepository,
        student_repository: StudentRepository,
        academic_year_repository: AcademicYearRepository,
    ) -> None:
        self.report_repository = report_repository
        self.fee_repository = fee_repository
        self.attendance_repository = attendance_repository
        self.student_repository = student_repository
        self.academic_year_repository = academic_year_repository

    def _resolve_year_id(self, academic_year_id: str | None) -> str | None:
        if academic_year_id:
            return academic_year_id
        active_year = self.academic_year_repository.get_active()
        return active_year.id if active_year else None

    def fee_summary(self, academic_year_id: str | None = None) -> dict:
        year_id = self._resolve_year_id(academic_year_id)
        total_collected, total_pending = self.report_repository.fee_summary(year_id)
        return {"total_collected": total_collected, "total_pending": total_pending}

    def fee_pending_details(self, academic_year_id: str | None = None) -> list[dict]:
        year_id = self._resolve_year_id(academic_year_id)
        rows = self.report_repository.fee_pending_details(year_id)
        results: list[dict] = []
        for student, record, class_room in rows:
            total_fee = self.fee_repository.get_total_fee_for_student(student.id, record.academic_year_id)
            total_paid = self.fee_repository.get_total_paid(student.id, record.academic_year_id)
            pending = max(total_fee - total_paid, Decimal("0"))
            if pending <= 0:
                continue
            results.append(
                {
                    "student_id": student.id,
                    "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
                    "class_name": class_room.name,
                    "total_fee": total_fee,
                    "total_paid": total_paid,
                    "pending": pending,
                }
            )
        return results

    def fee_pending_by_class(self, academic_year_id: str | None = None) -> list[dict]:
        grouped: dict[str, dict] = {}
        for row in self.fee_pending_details(academic_year_id):
            class_name = row["class_name"] or "Unassigned"
            item = grouped.setdefault(
                class_name,
                {
                    "class_name": class_name,
                    "student_count": 0,
                    "pending_total": Decimal("0"),
                    "collected_total": Decimal("0"),
                },
            )
            item["student_count"] += 1
            item["pending_total"] += row["pending"]
            item["collected_total"] += row["total_paid"]
        return sorted(grouped.values(), key=lambda item: item["pending_total"], reverse=True)

    def student_attendance_summary(self, *, month: int, year: int, academic_year_id: str | None = None) -> list[dict]:
        rows = self.attendance_repository.get_student_attendance_rows(
            month=month,
            year=year,
            academic_year_id=self._resolve_year_id(academic_year_id),
        )
        grouped: dict[str, dict] = defaultdict(
            lambda: {
                "entity_id": "",
                "entity_name": "",
                "present_count": 0,
                "absent_count": 0,
                "leave_count": 0,
                "attendance_percentage": 0.0,
            }
        )
        for row in rows:
            student = self.student_repository.get_by_id(row.student_id)
            if not student:
                continue
            item = grouped[row.student_id]
            item["entity_id"] = row.student_id
            item["entity_name"] = f"{student.first_name} {student.last_name or ''}".strip()
            if row.status == "PRESENT":
                item["present_count"] += 1
            elif row.status == "ABSENT":
                item["absent_count"] += 1
            else:
                item["leave_count"] += 1

        for item in grouped.values():
            total = item["present_count"] + item["absent_count"] + item["leave_count"]
            item["attendance_percentage"] = round((item["present_count"] / total) * 100, 2) if total else 0.0
        return list(grouped.values())

    def attendance_details(self, *, student_id: str, month: int, year: int) -> list[dict]:
        student = self.student_repository.get_by_id(student_id)
        if not student:
            raise NotFoundException("Student not found")
        rows = self.report_repository.student_attendance_details(student_id, month, year)
        return [{"attendance_date": row.attendance_date, "status": row.status} for row in rows]

    def teacher_payment_summary(self, academic_year_id: str | None = None) -> list[dict]:
        rows = self.report_repository.teacher_payment_summary(self._resolve_year_id(academic_year_id))
        results: list[dict] = []
        for teacher_id, teacher_name, contract_total, total_paid in rows:
            contract_total = Decimal(contract_total or 0)
            total_paid = Decimal(total_paid or 0)
            results.append(
                {
                    "teacher_id": teacher_id,
                    "teacher_name": teacher_name,
                    "contract_total": contract_total,
                    "total_paid": total_paid,
                    "pending_balance": max(contract_total - total_paid, Decimal("0")),
                }
            )
        return results

    def student_status_breakdown(self, academic_year_id: str | None = None) -> list[dict]:
        rows = self.report_repository.student_status_breakdown(self._resolve_year_id(academic_year_id))
        return [
            {
                "status": status.value if hasattr(status, "value") else str(status),
                "count": int(count),
            }
            for status, count in rows
        ]

    def monthly_finance_trend(self, *, calendar_year: int, academic_year_id: str | None = None) -> list[dict]:
        year_id = self._resolve_year_id(academic_year_id)
        fee_map = {
            int(month): Decimal(amount or 0)
            for month, amount in self.report_repository.monthly_fee_collection(
                calendar_year=calendar_year,
                academic_year_id=year_id,
            )
        }
        teacher_map = {
            int(month): Decimal(amount or 0)
            for month, amount in self.report_repository.monthly_teacher_payout(
                calendar_year=calendar_year,
                academic_year_id=year_id,
            )
        }
        return [
            {
                "month": month,
                "label": month_abbr[month],
                "fee_collected": fee_map.get(month, Decimal("0")),
                "teacher_paid": teacher_map.get(month, Decimal("0")),
                "net_cashflow": fee_map.get(month, Decimal("0")) - teacher_map.get(month, Decimal("0")),
            }
            for month in range(1, 13)
        ]

    def dashboard_overview(self, academic_year_id: str | None = None) -> dict:
        year_id = self._resolve_year_id(academic_year_id)
        total_collected, total_pending = self.report_repository.fee_summary(year_id)
        student_total, active_students = self.report_repository.student_overview(year_id)
        teacher_total, active_teachers = self.report_repository.teacher_overview()
        class_count, section_count = self.report_repository.reference_overview()
        teacher_payments = self.teacher_payment_summary(year_id)
        pending_students = self.fee_pending_details(year_id)
        student_status = self.student_status_breakdown(year_id)

        return {
            "student_total": student_total,
            "active_students": active_students,
            "teacher_total": teacher_total,
            "active_teachers": active_teachers,
            "class_count": class_count,
            "section_count": section_count,
            "fee_collected": total_collected,
            "fee_pending": total_pending,
            "pending_students": len(pending_students),
            "salary_pending": sum((item["pending_balance"] for item in teacher_payments), Decimal("0")),
            "student_status": student_status,
        }
