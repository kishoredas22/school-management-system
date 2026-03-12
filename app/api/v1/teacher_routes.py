"""Teacher endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.teacher_schema import TeacherContractCreate, TeacherCreate, TeacherPaymentCreate, TeacherUpdate
from app.services.teacher_service import TeacherService
from app.utils.helpers import success_response
from app.utils.receipt_generator import generate_salary_slip

router = APIRouter(prefix="/teachers", tags=["teachers"])


def _teacher_service(db):
    return TeacherService(
        TeacherRepository(db),
        ReferenceRepository(db),
        AcademicYearRepository(db),
        AttendanceRepository(db),
    )


@router.post("")
def create_teacher(
    payload: TeacherCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    teacher = _teacher_service(db).create_teacher(payload, actor_id=current_user.id)
    return success_response(data={"id": teacher.id}, message="Teacher created")


@router.get("")
def list_teachers(
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    db=Depends(get_db),
):
    teachers = _teacher_service(db).list_teachers()
    data = [
        {
            "id": item.id,
            "name": item.name,
            "phone": item.phone,
            "is_active": item.is_active,
            "assignment_count": len(item.assignments),
            "assignments": [
                {
                    "id": assignment.id,
                    "class_id": assignment.class_id,
                    "class_name": assignment.class_room.name if assignment.class_room else None,
                    "section_id": assignment.section_id,
                    "section_name": assignment.section.name if assignment.section else None,
                    "academic_year_id": assignment.academic_year_id,
                }
                for assignment in item.assignments
            ],
        }
        for item in teachers
    ]
    return success_response(data=data, message="Teachers retrieved")


@router.get("/contracts")
def list_teacher_contracts(
    teacher_id: UUID | None = None,
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    repository = TeacherRepository(db)
    contracts = repository.list_contracts(
        teacher_id=teacher_id if teacher_id else None,
        academic_year_id=year_id if year_id else None,
    )
    data = [
        {
            "id": item.id,
            "teacher_id": item.teacher_id,
            "teacher_name": item.teacher.name,
            "academic_year_id": item.academic_year_id,
            "academic_year_name": item.academic_year.name,
            "yearly_contract_amount": item.yearly_contract_amount,
            "monthly_salary": item.monthly_salary,
            "created_at": item.created_at,
        }
        for item in contracts
    ]
    return success_response(data=data, message="Teacher contracts retrieved")


@router.post("/contracts")
def create_teacher_contract(
    payload: TeacherContractCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    contract = _teacher_service(db).create_contract(payload, actor_id=current_user.id)
    return success_response(data={"id": contract.id}, message="Teacher contract created")


@router.post("/payments")
def record_teacher_payment(
    payload: TeacherPaymentCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    payment = _teacher_service(db).record_payment(payload, actor_id=current_user.id)
    return success_response(
        data={"id": payment.id, "receipt_number": payment.receipt_number},
        message="Teacher payment recorded",
    )


@router.get("/payments/{payment_id}/slip")
def get_salary_slip(
    payment_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    payload = _teacher_service(db).build_salary_slip_payload(payment_id)
    pdf = generate_salary_slip(payload)
    return Response(content=pdf, media_type="application/pdf")


@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: UUID,
    payload: TeacherUpdate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.TEACHER_MANAGE)),
    db=Depends(get_db),
):
    teacher = _teacher_service(db).update_teacher(teacher_id, payload, actor_id=current_user.id)
    return success_response(data={"id": teacher.id}, message="Teacher updated")
