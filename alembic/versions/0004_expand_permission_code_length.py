"""Expand permission code storage for newer IAM permissions."""

from alembic import op
import sqlalchemy as sa


revision = "0004_perm_code_expand"
down_revision = "0003_audit_review_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for constraint in inspector.get_check_constraints("user_permission_grants"):
        sqltext = constraint.get("sqltext") or ""
        if "permission_code" in sqltext:
            op.drop_constraint(constraint["name"], "user_permission_grants", type_="check")

    op.alter_column(
        "user_permission_grants",
        "permission_code",
        existing_type=sa.String(length=18),
        type_=sa.String(length=32),
        postgresql_using="permission_code::text",
    )


def downgrade() -> None:
    op.alter_column(
        "user_permission_grants",
        "permission_code",
        existing_type=sa.String(length=32),
        type_=sa.String(length=18),
        postgresql_using="permission_code::text",
    )
