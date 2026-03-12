"""Shared SQLAlchemy base classes."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative model."""


class TimestampMixin:
    """Reusable timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class UUIDPrimaryKeyMixin:
    """Reusable UUID primary key column."""

    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)


class SoftDeleteMixin:
    """Reusable soft-delete flag."""

    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
