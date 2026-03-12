"""Seed baseline reference and admin data."""

from datetime import date

from sqlalchemy import select

from app.core.config import settings
from app.core.permissions import allowed_permissions_for_role
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.academic_year import AcademicYear
from app.models.enums import LoginMode, RoleName
from app.models.reference import ClassRoom, Section
from app.models.role import Role
from app.models.user import User
from app.models.user_permission_grant import UserPermissionGrant


def seed_roles(db) -> None:
    for role_name in RoleName:
        exists = db.scalar(select(Role).where(Role.name == role_name.value))
        if not exists:
            db.add(Role(name=role_name.value, description=f"{role_name.value.replace('_', ' ').title()} role"))


def seed_super_admin(db) -> None:
    user = db.scalar(select(User).where(User.username == settings.initial_super_admin_username))
    if user:
        return
    role = db.scalar(select(Role).where(Role.name == RoleName.SUPER_ADMIN.value))
    user = User(
        username=settings.initial_super_admin_username,
        password_hash=hash_password(settings.initial_super_admin_password),
        login_mode=LoginMode.PASSWORD,
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add_all(
        [
            UserPermissionGrant(user_id=user.id, permission_code=permission)
            for permission in allowed_permissions_for_role(RoleName.SUPER_ADMIN)
        ]
    )


def seed_reference_data(db) -> None:
    classes = ["Class 1", "Class 2", "Class 3"]
    for class_name in classes:
        class_room = db.scalar(select(ClassRoom).where(ClassRoom.name == class_name))
        if not class_room:
            class_room = ClassRoom(name=class_name)
            db.add(class_room)
            db.flush()
        for section_name in ["A", "B"]:
            section = db.scalar(
                select(Section).where(Section.name == section_name, Section.class_id == class_room.id)
            )
            if not section:
                db.add(Section(name=section_name, class_id=class_room.id))


def seed_academic_year(db) -> None:
    year = db.scalar(select(AcademicYear).where(AcademicYear.name == "2025-2026"))
    if not year:
        db.add(
            AcademicYear(
                name="2025-2026",
                start_date=date(2025, 6, 1),
                end_date=date(2026, 3, 31),
                is_active=True,
                is_closed=False,
            )
        )


def main() -> None:
    db = SessionLocal()
    try:
        seed_roles(db)
        db.flush()
        seed_super_admin(db)
        seed_reference_data(db)
        seed_academic_year(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
