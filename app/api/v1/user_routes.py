"""User management endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.enums import RoleName
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService
from app.utils.helpers import success_response
from app.utils.pagination import build_pagination

router = APIRouter(prefix="/users", tags=["users"])


def _serialize_user(user):
    assignments = [
        {
            "class_name": item.class_room.name if item.class_room else None,
            "section_name": item.section.name if item.section else None,
            "academic_year_id": item.academic_year_id,
        }
        for item in (user.teacher_profile.assignments if user.teacher_profile else [])
    ]
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "login_mode": user.login_mode.value,
        "is_active": user.is_active,
        "role": user.role.name,
        "teacher_id": user.teacher_id,
        "teacher_name": user.teacher_profile.name if user.teacher_profile else None,
        "teacher_phone": user.teacher_profile.phone if user.teacher_profile else None,
        "teacher_assignment_count": len(assignments),
        "teacher_assignments": assignments,
        "permissions": sorted(grant.permission_code.value for grant in user.permission_grants),
    }


@router.get("/access-options")
def get_access_options(
    _=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = UserService(UserRepository(db), TeacherRepository(db))
    return success_response(data=service.get_access_options(), message="Access options retrieved")


@router.post("")
def create_user(
    payload: UserCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = UserService(UserRepository(db), TeacherRepository(db))
    result = service.create_user(
        username=payload.username,
        password=payload.password,
        email=payload.email,
        login_mode=payload.login_mode,
        role=payload.role,
        active=payload.active,
        teacher_id=payload.teacher_id,
        permissions=payload.permissions,
        actor_id=current_user.id,
    )
    return success_response(
        data={
            "user": _serialize_user(result.user),
            "email_link": result.email_link,
        },
        message="User created",
    )


@router.get("")
def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _=Depends(require_roles(RoleName.SUPER_ADMIN)),
    db=Depends(get_db),
):
    service = UserService(UserRepository(db), TeacherRepository(db))
    users, total = service.list_users(page=page, size=size)
    pagination = build_pagination(page, size, total, [_serialize_user(user) for user in users])
    return success_response(data=pagination.to_dict(), message="Users retrieved")
