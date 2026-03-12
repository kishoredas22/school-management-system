"""Common schema definitions."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema configured for SQLAlchemy ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class ApiResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str = "Operation successful"
    data: Any = None


class ApiErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error_code: str
    message: str
    details: dict[str, Any] = {}
