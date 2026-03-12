"""User data access layer."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.email_login_token import EmailLoginToken
from app.models.enums import RoleName
from app.models.role import Role
from app.models.teacher import Teacher, TeacherClassAssignment
from app.models.user import User
from app.models.user_permission_grant import UserPermissionGrant


class UserRepository:
    """Repository for user and role persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _user_query(self):
        return select(User).options(
            joinedload(User.role),
            joinedload(User.permission_grants),
            joinedload(User.teacher_profile)
            .joinedload(Teacher.assignments)
            .joinedload(TeacherClassAssignment.class_room),
            joinedload(User.teacher_profile)
            .joinedload(Teacher.assignments)
            .joinedload(TeacherClassAssignment.section),
        )

    def get_by_username(self, username: str) -> User | None:
        return (
            self.db.execute(self._user_query().where(User.username == username, User.is_deleted.is_(False)))
            .unique()
            .scalar_one_or_none()
        )

    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.execute(
                self._user_query().where(User.email == email, User.is_deleted.is_(False))
            )
            .unique()
            .scalar_one_or_none()
        )

    def get_by_id(self, user_id: str) -> User | None:
        return (
            self.db.execute(self._user_query().where(User.id == user_id, User.is_deleted.is_(False)))
            .unique()
            .scalar_one_or_none()
        )

    def list_users(self, *, page: int, size: int) -> tuple[list[User], int]:
        query = (
            self._user_query()
            .where(User.is_deleted.is_(False))
            .order_by(User.username)
        )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.execute(query.offset((page - 1) * size).limit(size)).unique().scalars().all()
        return items, total

    def get_by_teacher_id(self, teacher_id: str) -> User | None:
        return (
            self.db.execute(self._user_query().where(User.teacher_id == teacher_id, User.is_deleted.is_(False)))
            .unique()
            .scalar_one_or_none()
        )

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def get_role_by_name(self, role_name: RoleName | str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == str(role_name)))

    def list_roles(self) -> list[Role]:
        return self.db.scalars(select(Role).order_by(Role.name)).all()

    def replace_permission_grants(self, user: User, permissions: list[UserPermissionGrant]) -> None:
        user.permission_grants.clear()
        user.permission_grants.extend(permissions)
        self.db.flush()

    def create_email_login_token(self, token: EmailLoginToken) -> EmailLoginToken:
        self.db.add(token)
        self.db.flush()
        self.db.refresh(token)
        return token

    def get_email_login_token(self, token_hash: str) -> EmailLoginToken | None:
        return (
            self.db.execute(
                select(EmailLoginToken)
                .options(
                    joinedload(EmailLoginToken.user).joinedload(User.role),
                    joinedload(EmailLoginToken.user).joinedload(User.permission_grants),
                )
                .where(EmailLoginToken.token_hash == token_hash)
            )
            .unique()
            .scalar_one_or_none()
        )

    def mark_email_login_token_consumed(self, token: EmailLoginToken, consumed_at: datetime) -> None:
        token.consumed_at = consumed_at
        self.db.add(token)
        self.db.flush()
