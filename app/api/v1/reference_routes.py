"""Reference data endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.reference_repository import ReferenceRepository
from app.schemas.reference_schema import ClassCreate, SectionCreate
from app.services.reference_service import ReferenceService
from app.utils.helpers import success_response

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/classes")
def list_classes(
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    db=Depends(get_db),
):
    repository = ReferenceRepository(db)
    classes = repository.list_classes()
    data = [{"id": item.id, "name": item.name} for item in classes]
    return success_response(data=data, message="Classes retrieved")


@router.post("/classes")
def create_class(
    payload: ClassCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    class_room = ReferenceService(ReferenceRepository(db)).create_class(name=payload.name, actor_id=current_user.id)
    return success_response(data={"id": class_room.id, "name": class_room.name}, message="Class created")


@router.get("/sections")
def list_sections(
    class_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.DATA_ENTRY, RoleName.TEACHER)),
    db=Depends(get_db),
):
    repository = ReferenceRepository(db)
    sections = repository.list_sections(str(class_id) if class_id else None)
    data = [{"id": item.id, "name": item.name, "class_id": item.class_id} for item in sections]
    return success_response(data=data, message="Sections retrieved")


@router.post("/sections")
def create_section(
    payload: SectionCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    section = ReferenceService(ReferenceRepository(db)).create_section(
        name=payload.name,
        class_id=str(payload.class_id),
        actor_id=current_user.id,
    )
    return success_response(
        data={"id": section.id, "name": section.name, "class_id": section.class_id},
        message="Section created",
    )
