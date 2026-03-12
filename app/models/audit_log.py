"""Audit log model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AuditReviewStatus


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable audit log entry."""

    __tablename__ = "audit_logs"

    entity_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict | None] = mapped_column(JSON)
    performed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    review_status: Mapped[AuditReviewStatus] = mapped_column(
        Enum(AuditReviewStatus, native_enum=False),
        default=AuditReviewStatus.NOT_REQUIRED,
        nullable=False,
        index=True,
    )
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor = relationship("User", back_populates="audit_logs", foreign_keys=[performed_by])
    reviewer = relationship("User", back_populates="reviewed_audit_logs", foreign_keys=[reviewed_by])
