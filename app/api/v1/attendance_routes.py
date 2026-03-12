"""Attendance endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.attendance_schema import StudentAttendanceCreate, TeacherAttendanceCreate
from app.services.attendance_service import AttendanceService
from app.utils.helpers import success_response

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _attendance_service(db):
    return AttendanceService(
        AttendanceRepository(db),
        AcademicYearRepository(db),
        StudentRepository(db),
        TeacherRepository(db),
    )


@router.post("/students")
def mark_student_attendance(
    payload: StudentAttendanceCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    _=Depends(require_permissions(PermissionCode.ATTENDANCE_STUDENT)),
    db=Depends(get_db),
):
    records = _attendance_service(db).mark_student_attendance(payload, current_user=current_user)
    return success_response(data={"count": len(records)}, message="Student attendance recorded")


@router.get("/students")
def get_student_attendance_register(
    class_id: UUID,
    section_id: UUID,
    attendance_date: date = Query(alias="date"),
    q: str | None = Query(default=None, alias="q"),
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    _=Depends(require_permissions(PermissionCode.ATTENDANCE_STUDENT)),
    db=Depends(get_db),
):
    register = _attendance_service(db).get_student_register(
        class_id=class_id,
        section_id=section_id,
        attendance_date=attendance_date,
        current_user=current_user,
        search=q,
    )
    return success_response(data=register, message="Student attendance register retrieved")


@router.post("/teachers")
def mark_teacher_attendance(
    payload: TeacherAttendanceCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    _=Depends(require_permissions(PermissionCode.ATTENDANCE_TEACHER)),
    db=Depends(get_db),
):
    record = _attendance_service(db).mark_teacher_attendance(payload, actor_id=current_user.id)
    return success_response(data={"id": record.id}, message="Teacher attendance recorded")


@router.get("/teachers")
def list_teacher_attendance(
    attendance_date: date = Query(alias="date"),
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    __=Depends(require_permissions(PermissionCode.ATTENDANCE_TEACHER)),
    db=Depends(get_db),
):
    records = _attendance_service(db).list_teacher_attendance(attendance_date=attendance_date)
    return success_response(data=records, message="Teacher attendance retrieved")
