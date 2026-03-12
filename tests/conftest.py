"""Pytest fixtures."""

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_school_management.db"
os.environ["ENVIRONMENT"] = "test"

from app.core.database import get_db  # noqa: E402
from app.core.permissions import allowed_permissions_for_role  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.academic_year import AcademicYear  # noqa: E402
from app.models.enums import LoginMode, RoleName  # noqa: E402
from app.models.reference import ClassRoom, Section  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_permission_grant import UserPermissionGrant  # noqa: E402

TEST_DB_URL = "sqlite:///./test_school_management.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        roles = [Role(name=role.value, description=role.value) for role in RoleName]
        db.add_all(roles)
        db.flush()
        teacher_role = db.scalar(select(Role).where(Role.name == RoleName.TEACHER.value))
        admin_role = db.scalar(select(Role).where(Role.name == RoleName.ADMIN.value))
        super_admin_role = db.scalar(select(Role).where(Role.name == RoleName.SUPER_ADMIN.value))
        data_entry_role = db.scalar(select(Role).where(Role.name == RoleName.DATA_ENTRY.value))

        seeded_users = [
            (User(username="superadmin", password_hash=hash_password("password123"), login_mode=LoginMode.PASSWORD, role_id=super_admin_role.id, is_active=True), RoleName.SUPER_ADMIN),
            (User(username="admin", password_hash=hash_password("password123"), login_mode=LoginMode.PASSWORD, role_id=admin_role.id, is_active=True), RoleName.ADMIN),
            (User(username="teacher", password_hash=hash_password("password123"), login_mode=LoginMode.PASSWORD, role_id=teacher_role.id, is_active=True), RoleName.TEACHER),
            (User(username="data_entry", password_hash=hash_password("password123"), login_mode=LoginMode.PASSWORD, role_id=data_entry_role.id, is_active=True), RoleName.DATA_ENTRY),
        ]
        db.add_all([user for user, _ in seeded_users])
        db.flush()
        for user, role_name in seeded_users:
            db.add_all(
                [
                    UserPermissionGrant(user_id=user.id, permission_code=permission)
                    for permission in allowed_permissions_for_role(role_name)
                ]
            )

        class_room = ClassRoom(name="Class 1")
        db.add(class_room)
        db.flush()
        db.add(Section(name="A", class_id=class_room.id))
        db.add(
            AcademicYear(
                name="2025-2026",
                start_date=date(2025, 6, 1),
                end_date=date(2026, 3, 31),
                is_active=True,
                is_closed=False,
            )
        )
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def auth_headers(client: TestClient, username: str, password: str = "password123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
