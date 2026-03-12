"""Authentication business logic."""

import secrets
from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.core.permissions import effective_permissions_for_user
from app.core.security import create_access_token, hash_login_token, verify_password
from app.models.email_login_token import EmailLoginToken
from app.models.enums import LoginMode
from app.repositories.user_repository import UserRepository
from app.utils.helpers import utcnow

logger = get_logger(__name__)


class AuthService:
    """Authentication workflows."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def _serialize_auth_payload(self, user) -> dict[str, str | list[str]]:
        permissions = sorted(
            effective_permissions_for_user(
                role_name=user.role.name,
                assigned_permissions=[grant.permission_code.value for grant in user.permission_grants],
            )
        )

        return {
            "access_token": create_access_token(subject=user.username, role=user.role.name),
            "token_type": "bearer",
            "username": user.username,
            "role": user.role.name,
            "login_mode": user.login_mode.value,
            "permissions": permissions,
        }

    def login(self, *, username: str, password: str) -> dict[str, str | list[str]]:
        user = self.user_repository.get_by_username(username)
        if not user or user.is_deleted:
            logger.warning("login_failed", extra={"method": "POST", "path": "/auth/login"})
            raise AuthenticationException(message="Invalid username or password")
        if not user.is_active:
            raise AuthenticationException(message="Inactive user login blocked")
        if user.login_mode == LoginMode.EMAIL_LINK:
            raise AuthenticationException(message="This account uses email link sign-in only")
        if not user.password_hash or not verify_password(password, user.password_hash):
            logger.warning("login_failed", extra={"method": "POST", "path": "/auth/login"})
            raise AuthenticationException(message="Invalid username or password")

        return self._serialize_auth_payload(user)

    def request_email_login_link(self, *, email: str) -> dict:
        user = self.user_repository.get_by_email(email)
        if (
            not user
            or user.is_deleted
            or not user.is_active
            or user.login_mode != LoginMode.EMAIL_LINK
        ):
            return {"delivery": "accepted"}

        raw_token = secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(minutes=settings.email_login_link_expire_minutes)
        self.user_repository.create_email_login_token(
            EmailLoginToken(
                user_id=user.id,
                token_hash=hash_login_token(raw_token),
                purpose="LOGIN",
                expires_at=expires_at,
            )
        )
        self.user_repository.db.commit()
        return {
            "delivery": "preview_link",
            "email": user.email,
            "expires_at": expires_at,
            "login_url": f"{settings.frontend_app_url.rstrip('/')}/login?email_token={raw_token}",
        }

    def consume_email_login_link(self, *, token: str) -> dict[str, str | list[str]]:
        record = self.user_repository.get_email_login_token(hash_login_token(token))
        if not record or record.consumed_at is not None or record.expires_at < utcnow():
            raise AuthenticationException(message="Invalid or expired email login link")

        user = record.user
        if not user or user.is_deleted or not user.is_active or user.login_mode != LoginMode.EMAIL_LINK:
            raise AuthenticationException(message="Email link sign-in is not available for this account")

        self.user_repository.mark_email_login_token_consumed(record, consumed_at=utcnow())
        self.user_repository.db.commit()
        return self._serialize_auth_payload(user)
