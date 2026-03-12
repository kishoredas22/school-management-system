"""Authentication schemas."""

import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    """Login request body."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Login response payload."""

    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    login_mode: str
    permissions: list[str] = Field(default_factory=list)


class EmailLinkRequest(BaseModel):
    """Request a one-time email login link."""

    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Invalid email address")
        return normalized


class EmailLinkConsumeRequest(BaseModel):
    """Consume a one-time email login link."""

    token: str = Field(min_length=20)
