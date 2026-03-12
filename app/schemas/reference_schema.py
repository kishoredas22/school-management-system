"""Reference-data schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    """Create-class request."""

    name: str = Field(min_length=1, max_length=50)


class SectionCreate(BaseModel):
    """Create-section request."""

    name: str = Field(min_length=1, max_length=10)
    class_id: UUID
