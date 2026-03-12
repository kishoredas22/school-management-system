"""Student endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.student_schema import StudentCreate, StudentPromotionRequest, StudentStatusUpdate, StudentUpdate
from app.services.promotion_service import PromotionService
from app.services.student_service import StudentService
from app.utils.helpers import success_response

router = APIRouter(prefix="/students", tags=["students"])


def _student_service(db):
    return StudentService(StudentRepository(db), ReferenceRepository(db), AcademicYearRepository(db))


@router.post("")
def create_student(
    payload: StudentCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    _=Depends(require_permissions(PermissionCode.STUDENT_RECORDS)),
    db=Depends(get_db),
):
    student = _student_service(db).create_student(payload, actor_id=current_user.id)
    return success_response(data={"id": student.id}, message="Student created")


@router.get("")
def list_students(
    class_id: UUID | None = None,
    section_id: UUID | None = None,
    status: str | None = None,
    q: str | None = Query(default=None, alias="q"),
    year_id: UUID | None = Query(default=None, alias="year_id"),
    include_inactive: bool = Query(default=False, alias="include_inactive"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    __=Depends(require_permissions(PermissionCode.STUDENT_RECORDS)),
    db=Depends(get_db),
):
    data = _student_service(db).list_students(
        academic_year_id=year_id,
        class_id=class_id,
        section_id=section_id,
        status=status,
        search=q,
        include_inactive=include_inactive,
        page=page,
        size=size,
    )
    return success_response(data=data.to_dict(), message="Students retrieved")


@router.put("/{student_id}")
def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    _=Depends(require_permissions(PermissionCode.STUDENT_RECORDS)),
    db=Depends(get_db),
):
    student = _student_service(db).update_student(student_id, payload, actor_id=current_user.id)
    return success_response(data={"id": student.id}, message="Student updated")


@router.put("/{student_id}/status")
def update_student_status(
    student_id: UUID,
    payload: StudentStatusUpdate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.STUDENT_STATUS)),
    db=Depends(get_db),
):
    student = _student_service(db).update_status(
        student_id,
        payload.status,
        actor_id=current_user.id,
        actor_role=current_user.role.name,
    )
    return success_response(data={"id": student.id, "status": student.status}, message="Student status updated")


@router.post("/promote")
def promote_students(
    payload: StudentPromotionRequest,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.STUDENT_STATUS)),
    db=Depends(get_db),
):
    service = PromotionService(StudentRepository(db), AcademicYearRepository(db))
    result = service.promote_students(payload, actor_id=current_user.id)
    return success_response(data=result, message="Promotion workflow completed")
