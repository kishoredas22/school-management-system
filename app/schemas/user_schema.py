"""User management schemas."""

import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCreate(BaseModel):
    """Create-user request schema."""

    username: str = Field(min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=8)
    email: str | None = Field(default=None, max_length=255)
    login_mode: str = "PASSWORD"
    role: str
    active: bool = True
    teacher_id: UUID | None = None
    permissions: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Invalid email address")
        return normalized


class UserRead(ORMModel):
    """User response schema."""

    id: UUID
    username: str
    email: str | None = None
    login_mode: str
    is_active: bool
    role: str
    teacher_id: UUID | None = None
    permissions: list[str] = Field(default_factory=list)
