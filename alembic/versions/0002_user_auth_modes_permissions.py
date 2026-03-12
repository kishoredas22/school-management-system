"""Add user auth modes, email login links, and permission grants."""

from datetime import UTC, datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0002_user_auth_modes_permissions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


login_mode_enum = sa.Enum("PASSWORD", "EMAIL_LINK", name="login_mode", native_enum=False)
permission_code_enum = sa.Enum(
    "USER_MANAGE",
    "TEACHER_MANAGE",
    "STUDENT_RECORDS",
    "STUDENT_STATUS",
    "ATTENDANCE_STUDENT",
    "ATTENDANCE_TEACHER",
    "FEE_MANAGE",
    "REPORT_VIEW",
    "AUDIT_VIEW",
    "REFERENCE_MANAGE",
    name="permission_code",
    native_enum=False,
)

ROLE_DEFAULTS = {
    "SUPER_ADMIN": [
        "USER_MANAGE",
        "TEACHER_MANAGE",
        "STUDENT_RECORDS",
        "STUDENT_STATUS",
        "ATTENDANCE_STUDENT",
        "ATTENDANCE_TEACHER",
        "FEE_MANAGE",
        "REPORT_VIEW",
        "AUDIT_VIEW",
        "REFERENCE_MANAGE",
    ],
    "ADMIN": [
        "TEACHER_MANAGE",
        "STUDENT_RECORDS",
        "STUDENT_STATUS",
        "ATTENDANCE_STUDENT",
        "ATTENDANCE_TEACHER",
        "FEE_MANAGE",
        "REPORT_VIEW",
        "REFERENCE_MANAGE",
    ],
    "DATA_ENTRY": [
        "STUDENT_RECORDS",
        "ATTENDANCE_STUDENT",
        "ATTENDANCE_TEACHER",
        "FEE_MANAGE",
    ],
    "TEACHER": [
        "STUDENT_RECORDS",
        "ATTENDANCE_STUDENT",
    ],
}


def upgrade() -> None:
    bind = op.get_bind()
    login_mode_enum.create(bind, checkfirst=True)
    permission_code_enum.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("login_mode", login_mode_enum, nullable=False, server_default="PASSWORD"))
    op.alter_column("users", "password_hash", existing_type=sa.Text(), nullable=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "user_permission_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission_code", permission_code_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "permission_code", name="uq_user_permission_code"),
    )
    op.create_index(op.f("ix_user_permission_grants_user_id"), "user_permission_grants", ["user_id"], unique=False)

    op.create_table(
        "email_login_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_email_login_tokens_user_id"), "email_login_tokens", ["user_id"], unique=False)

    op.alter_column("users", "login_mode", server_default=None)

    users_table = sa.table(
        "users",
        sa.column("id", sa.Uuid()),
        sa.column("role_id", sa.Uuid()),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(length=50)),
    )
    grants_table = sa.table(
        "user_permission_grants",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("permission_code", permission_code_enum),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_users = bind.execute(
        sa.select(users_table.c.id, roles_table.c.name).select_from(
            users_table.join(roles_table, users_table.c.role_id == roles_table.c.id)
        )
    ).all()

    now = datetime.now(UTC)
    grant_rows = []
    for user_id, role_name in existing_users:
        for permission_code in ROLE_DEFAULTS.get(role_name, []):
            grant_rows.append(
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "permission_code": permission_code,
                    "created_at": now,
                    "updated_at": None,
                }
            )

    if grant_rows:
        op.bulk_insert(grants_table, grant_rows)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_login_tokens_user_id"), table_name="email_login_tokens")
    op.drop_table("email_login_tokens")

    op.drop_index(op.f("ix_user_permission_grants_user_id"), table_name="user_permission_grants")
    op.drop_table("user_permission_grants")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "login_mode")
    op.drop_column("users", "email")
    op.alter_column("users", "password_hash", existing_type=sa.Text(), nullable=False)

    permission_code_enum.drop(op.get_bind(), checkfirst=False)
    login_mode_enum.drop(op.get_bind(), checkfirst=False)
