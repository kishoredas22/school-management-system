"""Reporting endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.fee_repository import FeeRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.student_repository import StudentRepository
from app.services.report_service import ReportService
from app.utils.csv_export import build_csv_response
from app.utils.helpers import success_response

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_service(db):
    return ReportService(
        ReportRepository(db),
        FeeRepository(db),
        AttendanceRepository(db),
        StudentRepository(db),
        AcademicYearRepository(db),
    )


def _serialize_monthly_report_filename(prefix: str, year_id: UUID | None = None, *, month: int | None = None, year: int | None = None) -> str:
    parts = [prefix]
    if year_id:
        parts.append(str(year_id))
    if year:
        parts.append(str(year))
    if month:
        parts.append(f"{month:02d}")
    return "-".join(parts) + ".csv"


@router.get("/dashboard")
def get_dashboard_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).dashboard_overview(year_id)
    return success_response(data=report, message="Dashboard report retrieved")


@router.get("/finance/trend")
def get_finance_trend_report(
    calendar_year: int = Query(ge=2000, le=2100),
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).monthly_finance_trend(calendar_year=calendar_year, academic_year_id=year_id)
    return success_response(data=report, message="Finance trend report retrieved")


@router.get("/students/status")
def get_student_status_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).student_status_breakdown(year_id)
    return success_response(data=report, message="Student status report retrieved")


@router.get("/fees")
def get_fee_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).fee_summary(year_id)
    return success_response(data=report, message="Fee report retrieved")


@router.get("/fees/pending")
def get_pending_fee_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).fee_pending_details(year_id)
    return success_response(data=report, message="Pending fee report retrieved")


@router.get("/fees/pending/by-class")
def get_pending_fee_by_class_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).fee_pending_by_class(year_id)
    return success_response(data=report, message="Class fee balance report retrieved")


@router.get("/fees/pending/export")
def export_pending_fee_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).fee_pending_details(year_id)
    return build_csv_response(
        filename=_serialize_monthly_report_filename("pending-fees", year_id),
        headers=["Student", "Class", "Total Fee", "Paid", "Pending"],
        rows=[
            [
                row["student_name"],
                row["class_name"],
                row["total_fee"],
                row["total_paid"],
                row["pending"],
            ]
            for row in report
        ],
    )


@router.get("/attendance/students")
def get_student_attendance_report(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).student_attendance_summary(month=month, year=year, academic_year_id=year_id)
    return success_response(data=report, message="Attendance report retrieved")


@router.get("/attendance/students/export")
def export_student_attendance_report(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).student_attendance_summary(month=month, year=year, academic_year_id=year_id)
    return build_csv_response(
        filename=_serialize_monthly_report_filename("student-attendance", year_id, month=month, year=year),
        headers=["Student", "Present", "Absent", "Leave", "Attendance Percentage"],
        rows=[
            [
                row["entity_name"],
                row["present_count"],
                row["absent_count"],
                row["leave_count"],
                row["attendance_percentage"],
            ]
            for row in report
        ],
    )


@router.get("/attendance/details")
def get_attendance_details(
    student_id: UUID,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).attendance_details(student_id=student_id, month=month, year=year)
    return success_response(data=report, message="Attendance detail retrieved")


@router.get("/teacher-payments")
def get_teacher_payment_report(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).teacher_payment_summary(year_id)
    return success_response(data=report, message="Teacher payment report retrieved")


@router.get("/teacher-payments/details")
def get_teacher_payment_details(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).teacher_payment_summary(year_id)
    return success_response(data=report, message="Teacher payment details retrieved")


@router.get("/teacher-payments/export")
def export_teacher_payment_details(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    report = _report_service(db).teacher_payment_summary(year_id)
    return build_csv_response(
        filename=_serialize_monthly_report_filename("teacher-payments", year_id),
        headers=["Teacher", "Contract Total", "Paid", "Pending Balance"],
        rows=[
            [
                row["teacher_name"],
                row["contract_total"],
                row["total_paid"],
                row["pending_balance"],
            ]
            for row in report
        ],
    )
