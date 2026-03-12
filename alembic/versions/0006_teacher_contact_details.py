"""Add teacher email contact details."""

from alembic import op
import sqlalchemy as sa


revision = "0006_teacher_contact_details"
down_revision = "0005_academic_mgmt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teachers", sa.Column("email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("teachers", "email")
