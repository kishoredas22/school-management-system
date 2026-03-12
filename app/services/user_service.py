"""User management business logic."""

import secrets
from dataclasses import dataclass
from datetime import timedelta

from app.core.config import settings
from app.core.permissions import allowed_permissions_for_role, serialize_permission_catalog, serialize_role_defaults
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import hash_login_token, hash_password
from app.models.email_login_token import EmailLoginToken
from app.models.enums import LoginMode, PermissionCode, RoleName
from app.models.user import User
from app.models.user_permission_grant import UserPermissionGrant
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict, utcnow


@dataclass
class UserCreationResult:
    user: User
    email_link: dict | None = None


class UserService:
    """Business logic for user management."""

    def __init__(self, user_repository: UserRepository, teacher_repository: TeacherRepository) -> None:
        self.user_repository = user_repository
        self.teacher_repository = teacher_repository

    def _resolve_role(self, role: str) -> RoleName:
        try:
            return RoleName(role)
        except ValueError as exc:
            raise ValidationException("Invalid role supplied") from exc

    def _resolve_login_mode(self, login_mode: str) -> LoginMode:
        try:
            return LoginMode(login_mode)
        except ValueError as exc:
            raise ValidationException("Invalid login mode supplied") from exc

    def _resolve_permissions(self, *, role_name: RoleName, requested: list[str]) -> list[PermissionCode]:
        allowed = set(allowed_permissions_for_role(role_name))
        if role_name == RoleName.SUPER_ADMIN:
            return list(allowed_permissions_for_role(role_name))

        if not requested:
            return list(allowed_permissions_for_role(role_name))

        resolved: list[PermissionCode] = []
        seen: set[PermissionCode] = set()
        for item in requested:
            try:
                code = PermissionCode(item)
            except ValueError as exc:
                raise ValidationException(f"Invalid permission supplied: {item}") from exc
            if code not in allowed:
                raise ValidationException(f"Permission {code.value} is not allowed for role {role_name.value}")
            if code not in seen:
                resolved.append(code)
                seen.add(code)
        return resolved

    def _issue_email_login_link(self, *, user: User, purpose: str = "WELCOME") -> dict:
        raw_token = secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(minutes=settings.email_login_link_expire_minutes)
        self.user_repository.create_email_login_token(
            EmailLoginToken(
                user_id=user.id,
                token_hash=hash_login_token(raw_token),
                purpose=purpose,
                expires_at=expires_at,
            )
        )
        return {
            "email": user.email,
            "delivery": "preview_link",
            "purpose": purpose,
            "expires_at": expires_at,
            "login_url": f"{settings.frontend_app_url.rstrip('/')}/login?email_token={raw_token}",
        }

    def create_user(
        self,
        *,
        username: str,
        password: str | None,
        email: str | None,
        login_mode: str,
        role: str,
        active: bool,
        teacher_id: str | None,
        permissions: list[str],
        actor_id: str,
    ) -> UserCreationResult:
        username = username.strip()
        if self.user_repository.get_by_username(username):
            raise ConflictException("Username already exists")

        if email and self.user_repository.get_by_email(email):
            raise ConflictException("Email already exists")

        role_name = self._resolve_role(role)
        resolved_login_mode = self._resolve_login_mode(login_mode)

        if role_name == RoleName.TEACHER:
            if not teacher_id:
                raise ValidationException("Teacher role requires a linked teacher profile")

            teacher = self.teacher_repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundException("Teacher profile not found")
            if self.user_repository.get_by_teacher_id(teacher_id):
                raise ConflictException("Teacher profile is already linked to another user")
        elif teacher_id:
            raise ValidationException("Teacher profile link is allowed only for teacher role")

        if role_name == RoleName.SUPER_ADMIN and resolved_login_mode != LoginMode.PASSWORD:
            raise ValidationException("Super admin accounts must use password login")

        if resolved_login_mode == LoginMode.EMAIL_LINK and not email:
            raise ValidationException("Email-link login requires an email address")
        if resolved_login_mode == LoginMode.PASSWORD and not password:
            raise ValidationException("Password login requires a password")

        role_record = self.user_repository.get_role_by_name(role_name)
        if not role_record:
            raise NotFoundException("Role not found")

        permission_codes = self._resolve_permissions(role_name=role_name, requested=permissions)
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password) if password else None,
            login_mode=resolved_login_mode,
            role_id=role_record.id,
            is_active=active,
            teacher_id=teacher_id,
        )
        created = self.user_repository.create(user)
        self.user_repository.replace_permission_grants(
            created,
            [UserPermissionGrant(user_id=created.id, permission_code=code) for code in permission_codes],
        )
        email_link = self._issue_email_login_link(user=created) if resolved_login_mode == LoginMode.EMAIL_LINK else None
        log_audit_event(
            self.user_repository.db,
            entity_name="USER",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value={
                **model_to_dict(created, exclude={"password_hash"}),
                "permissions": [code.value for code in permission_codes],
            },
        )
        self.user_repository.db.commit()
        return UserCreationResult(user=created, email_link=email_link)

    def list_users(self, *, page: int, size: int) -> tuple[list[User], int]:
        return self.user_repository.list_users(page=page, size=size)

    def get_access_options(self) -> dict:
        return {
            "permissions": serialize_permission_catalog(),
            "default_permissions_by_role": serialize_role_defaults(),
            "login_modes": [mode.value for mode in LoginMode],
        }
