"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.permissions import effective_permissions_for_user
from app.core.security import decode_token
from app.models.enums import PermissionCode, RoleName
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Resolve the authenticated user from the JWT token."""

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthenticationException(message="Invalid or expired token") from exc

    username = payload.get("sub")
    if not username:
        raise AuthenticationException(message="Invalid token payload")

    user = UserRepository(db).get_by_username(username)
    if not user or user.is_deleted or not user.is_active:
        raise AuthenticationException(message="Inactive or unknown user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: RoleName):
    """Return a dependency that validates the caller role."""

    def dependency(current_user: CurrentUser) -> User:
        if current_user.role.name not in allowed_roles:
            raise AuthorizationException(message="You do not have access to this resource")
        return current_user

    return dependency


def get_effective_permissions(user: User) -> set[str]:
    """Return the active permission codes for a user."""

    return effective_permissions_for_user(
        role_name=user.role.name,
        assigned_permissions=[grant.permission_code.value for grant in user.permission_grants],
    )


def require_permissions(*required_permissions: PermissionCode):
    """Return a dependency that validates explicit user permissions."""

    def dependency(current_user: CurrentUser) -> User:
        effective = get_effective_permissions(current_user)
        missing = [permission for permission in required_permissions if permission.value not in effective]
        if missing:
            raise AuthorizationException(message="You do not have access to this resource")
        return current_user

    return dependency


def require_any_permissions(*required_permissions: PermissionCode):
    """Return a dependency that validates at least one of the supplied permissions."""

    def dependency(current_user: CurrentUser) -> User:
        effective = get_effective_permissions(current_user)
        if not any(permission.value in effective for permission in required_permissions):
            raise AuthorizationException(message="You do not have access to this resource")
        return current_user

    return dependency
