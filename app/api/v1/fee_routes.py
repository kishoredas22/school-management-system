"""Fee endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.fee_repository import FeeRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.fee_schema import FeePaymentCreate, FeeStructureCreate
from app.services.fee_service import FeeService
from app.utils.helpers import success_response
from app.utils.receipt_generator import generate_fee_receipt

router = APIRouter(prefix="/fees", tags=["fees"])


def _fee_service(db):
    return FeeService(
        FeeRepository(db),
        StudentRepository(db),
        AcademicYearRepository(db),
        ReferenceRepository(db),
    )


@router.post("/structures")
def create_fee_structure(
    payload: FeeStructureCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.FEE_MANAGE)),
    db=Depends(get_db),
):
    structure = _fee_service(db).create_fee_structure(payload, actor_id=current_user.id)
    return success_response(data={"id": structure.id}, message="Fee structure created")


@router.get("/structures")
def list_fee_structures(
    class_id: UUID,
    year_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    __=Depends(require_permissions(PermissionCode.FEE_MANAGE)),
    db=Depends(get_db),
):
    repository = FeeRepository(db)
    structures = repository.get_structures_for_class_year(str(class_id), str(year_id))
    data = [
        {
            "id": item.id,
            "class_id": item.class_id,
            "academic_year_id": item.academic_year_id,
            "fee_name": item.fee_name,
            "amount": item.amount,
            "fee_type": item.fee_type,
            "is_active": item.is_active,
        }
        for item in structures
    ]
    return success_response(data=data, message="Fee structures retrieved")


@router.post("/payments")
def record_fee_payment(
    payload: FeePaymentCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    _=Depends(require_permissions(PermissionCode.FEE_MANAGE)),
    db=Depends(get_db),
):
    payment = _fee_service(db).record_payment(payload, actor_id=current_user.id)
    return success_response(
        data={"id": payment.id, "receipt_number": payment.receipt_number},
        message="Fee payment recorded",
    )


@router.get("/payments/student/{student_id}")
def get_student_fee_summary(
    student_id: UUID,
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    __=Depends(require_permissions(PermissionCode.FEE_MANAGE)),
    db=Depends(get_db),
):
    summary = _fee_service(db).get_student_fee_summary(student_id, academic_year_id=year_id)
    return success_response(data=summary, message="Student fee summary retrieved")


@router.get("/payments/{payment_id}/receipt")
def get_fee_receipt(
    payment_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY)),
    __=Depends(require_permissions(PermissionCode.FEE_MANAGE)),
    db=Depends(get_db),
):
    payload = _fee_service(db).build_fee_receipt_payload(payment_id)
    pdf = generate_fee_receipt(payload)
    return Response(content=pdf, media_type="application/pdf")
