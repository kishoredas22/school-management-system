"""User model."""

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LoginMode


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Application user."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    login_mode: Mapped[LoginMode] = mapped_column(
        Enum(LoginMode, native_enum=False),
        default=LoginMode.PASSWORD,
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    teacher_id: Mapped[str | None] = mapped_column(ForeignKey("teachers.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="actor", foreign_keys="AuditLog.performed_by")
    reviewed_audit_logs = relationship(
        "AuditLog",
        back_populates="reviewer",
        foreign_keys="AuditLog.reviewed_by",
    )
    teacher_profile = relationship("Teacher", back_populates="user_accounts")
    permission_grants = relationship("UserPermissionGrant", back_populates="user", cascade="all, delete-orphan")
    email_login_tokens = relationship("EmailLoginToken", back_populates="user", cascade="all, delete-orphan")
