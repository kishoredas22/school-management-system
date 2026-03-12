"""Add audit review governance fields."""

from alembic import op
import sqlalchemy as sa


revision = "0003_audit_review_governance"
down_revision = "0002_user_auth_modes_permissions"
branch_labels = None
depends_on = None


audit_review_status_enum = sa.Enum(
    "NOT_REQUIRED",
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="auditreviewstatus",
    native_enum=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    audit_review_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "audit_logs",
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "audit_logs",
        sa.Column(
            "review_status",
            audit_review_status_enum,
            nullable=False,
            server_default="NOT_REQUIRED",
        ),
    )
    op.add_column("audit_logs", sa.Column("review_note", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("reviewed_by", sa.Uuid(), nullable=True))
    op.add_column("audit_logs", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_audit_logs_requires_review"), "audit_logs", ["requires_review"], unique=False)
    op.create_index(op.f("ix_audit_logs_review_status"), "audit_logs", ["review_status"], unique=False)
    op.create_index(op.f("ix_audit_logs_reviewed_by"), "audit_logs", ["reviewed_by"], unique=False)
    op.create_foreign_key(
        "fk_audit_logs_reviewed_by_users",
        "audit_logs",
        "users",
        ["reviewed_by"],
        ["id"],
    )

    op.alter_column("audit_logs", "requires_review", server_default=None)
    op.alter_column("audit_logs", "review_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_audit_logs_reviewed_by_users", "audit_logs", type_="foreignkey")
    op.drop_index(op.f("ix_audit_logs_reviewed_by"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_review_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_requires_review"), table_name="audit_logs")
    op.drop_column("audit_logs", "reviewed_at")
    op.drop_column("audit_logs", "reviewed_by")
    op.drop_column("audit_logs", "review_note")
    op.drop_column("audit_logs", "review_status")
    op.drop_column("audit_logs", "requires_review")
    audit_review_status_enum.drop(op.get_bind(), checkfirst=False)
