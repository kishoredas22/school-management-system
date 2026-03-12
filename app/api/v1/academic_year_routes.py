"""Academic year endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.enums import RoleName
from app.repositories.academic_year_repository import AcademicYearRepository
from app.schemas.academic_year_schema import AcademicYearCreate
from app.services.academic_year_service import AcademicYearService
from app.utils.helpers import success_response

router = APIRouter(prefix="/academic-years", tags=["academic-years"])


def _serialize_year(academic_year):
    return {
        "id": academic_year.id,
        "name": academic_year.name,
        "start_date": academic_year.start_date,
        "end_date": academic_year.end_date,
        "is_active": academic_year.is_active,
        "is_closed": academic_year.is_closed,
    }


@router.post("")
def create_academic_year(
    payload: AcademicYearCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = AcademicYearService(AcademicYearRepository(db))
    academic_year = service.create_academic_year(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        actor_id=current_user.id,
    )
    return success_response(data=_serialize_year(academic_year), message="Academic year created")


@router.get("")
def list_academic_years(
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    db=Depends(get_db),
):
    service = AcademicYearService(AcademicYearRepository(db))
    years = service.list_academic_years()
    return success_response(data=[_serialize_year(item) for item in years], message="Academic years retrieved")


@router.put("/{academic_year_id}/close")
def close_academic_year(
    academic_year_id: UUID,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = AcademicYearService(AcademicYearRepository(db))
    academic_year = service.close_academic_year(academic_year_id=academic_year_id, actor_id=current_user.id)
    return success_response(data=_serialize_year(academic_year), message="Academic year closed")


@router.put("/{academic_year_id}/activate")
def activate_academic_year(
    academic_year_id: UUID,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = AcademicYearService(AcademicYearRepository(db))
    academic_year = service.activate_academic_year(academic_year_id=academic_year_id, actor_id=current_user.id)
    return success_response(data=_serialize_year(academic_year), message="Academic year activated")
