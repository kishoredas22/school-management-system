"""User-level permission grants."""

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PermissionCode


class UserPermissionGrant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Explicit permission grant for a user."""

    __tablename__ = "user_permission_grants"
    __table_args__ = (UniqueConstraint("user_id", "permission_code", name="uq_user_permission_code"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    permission_code: Mapped[PermissionCode] = mapped_column(
        Enum(PermissionCode, native_enum=False, length=32, create_constraint=False),
        nullable=False,
    )

    user = relationship("User", back_populates="permission_grants")
