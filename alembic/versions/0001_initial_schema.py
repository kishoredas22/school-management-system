"""Initial schema."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum(
    "SUPER_ADMIN",
    "ADMIN",
    "TEACHER",
    "DATA_ENTRY",
    name="role_name",
    native_enum=False,
)
student_status_enum = sa.Enum(
    "ACTIVE",
    "PASSED_OUT",
    "TOOK_TC",
    "INACTIVE",
    name="student_status",
    native_enum=False,
)
attendance_status_enum = sa.Enum(
    "PRESENT",
    "ABSENT",
    "LEAVE",
    name="attendance_status",
    native_enum=False,
)
payment_mode_enum = sa.Enum("CASH", "BANK", "UPI", name="payment_mode", native_enum=False)
fee_type_enum = sa.Enum("ONE_TIME", "RECURRING", name="fee_type", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "academic_years",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "classes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "teachers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=10), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sections_class_id"), "sections", ["class_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.String(length=50), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("guardian_name", sa.String(length=150), nullable=True),
        sa.Column("guardian_phone", sa.String(length=20), nullable=True),
        sa.Column("status", student_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_students_status"), "students", ["status"], unique=False)
    op.create_index(op.f("ix_students_student_id"), "students", ["student_id"], unique=False)

    op.create_table(
        "teacher_class_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("academic_year_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_class_assignments_teacher_id"), "teacher_class_assignments", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_teacher_class_assignments_class_id"), "teacher_class_assignments", ["class_id"], unique=False)

    op.create_table(
        "student_academic_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("promotion_status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_student_academic_records_academic_year_id"), "student_academic_records", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_student_academic_records_class_id"), "student_academic_records", ["class_id"], unique=False)
    op.create_index(op.f("ix_student_academic_records_section_id"), "student_academic_records", ["section_id"], unique=False)
    op.create_index(op.f("ix_student_academic_records_student_id"), "student_academic_records", ["student_id"], unique=False)
    op.create_index("idx_student_year", "student_academic_records", ["student_id", "academic_year_id"], unique=False)

    op.create_table(
        "teacher_contracts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("yearly_contract_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("monthly_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_contracts_academic_year_id"), "teacher_contracts", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_teacher_contracts_teacher_id"), "teacher_contracts", ["teacher_id"], unique=False)

    op.create_table(
        "fee_structures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("fee_name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee_type", fee_type_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fee_structures_academic_year_id"), "fee_structures", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_fee_structures_class_id"), "fee_structures", ["class_id"], unique=False)

    op.create_table(
        "teacher_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_mode", payment_mode_enum, nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("receipt_number", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["teacher_contracts.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("receipt_number"),
    )
    op.create_index(op.f("ix_teacher_payments_contract_id"), "teacher_payments", ["contract_id"], unique=False)
    op.create_index(op.f("ix_teacher_payments_receipt_number"), "teacher_payments", ["receipt_number"], unique=True)
    op.create_index(op.f("ix_teacher_payments_teacher_id"), "teacher_payments", ["teacher_id"], unique=False)

    op.create_table(
        "fee_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("fee_structure_id", sa.Uuid(), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_mode", payment_mode_enum, nullable=False),
        sa.Column("receipt_number", sa.String(length=50), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["fee_structure_id"], ["fee_structures.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("receipt_number"),
    )
    op.create_index(op.f("ix_fee_payments_academic_year_id"), "fee_payments", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_fee_payments_fee_structure_id"), "fee_payments", ["fee_structure_id"], unique=False)
    op.create_index(op.f("ix_fee_payments_receipt_number"), "fee_payments", ["receipt_number"], unique=True)
    op.create_index(op.f("ix_fee_payments_student_id"), "fee_payments", ["student_id"], unique=False)

    op.create_table(
        "student_attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", attendance_status_enum, nullable=False),
        sa.Column("marked_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["marked_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_student_attendance_academic_year_id"), "student_attendance", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_student_attendance_attendance_date"), "student_attendance", ["attendance_date"], unique=False)
    op.create_index(op.f("ix_student_attendance_student_id"), "student_attendance", ["student_id"], unique=False)

    op.create_table(
        "teacher_attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", attendance_status_enum, nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_attendance_academic_year_id"), "teacher_attendance", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_teacher_attendance_attendance_date"), "teacher_attendance", ["attendance_date"], unique=False)
    op.create_index(op.f("ix_teacher_attendance_teacher_id"), "teacher_attendance", ["teacher_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_name", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("performed_by", sa.Uuid(), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_entity_name"), "audit_logs", ["entity_name"], unique=False)
    op.create_index(op.f("ix_audit_logs_performed_by"), "audit_logs", ["performed_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_performed_by"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_name"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_teacher_attendance_teacher_id"), table_name="teacher_attendance")
    op.drop_index(op.f("ix_teacher_attendance_attendance_date"), table_name="teacher_attendance")
    op.drop_index(op.f("ix_teacher_attendance_academic_year_id"), table_name="teacher_attendance")
    op.drop_table("teacher_attendance")

    op.drop_index(op.f("ix_student_attendance_student_id"), table_name="student_attendance")
    op.drop_index(op.f("ix_student_attendance_attendance_date"), table_name="student_attendance")
    op.drop_index(op.f("ix_student_attendance_academic_year_id"), table_name="student_attendance")
    op.drop_table("student_attendance")

    op.drop_index(op.f("ix_fee_payments_student_id"), table_name="fee_payments")
    op.drop_index(op.f("ix_fee_payments_receipt_number"), table_name="fee_payments")
    op.drop_index(op.f("ix_fee_payments_fee_structure_id"), table_name="fee_payments")
    op.drop_index(op.f("ix_fee_payments_academic_year_id"), table_name="fee_payments")
    op.drop_table("fee_payments")

    op.drop_index(op.f("ix_teacher_payments_teacher_id"), table_name="teacher_payments")
    op.drop_index(op.f("ix_teacher_payments_receipt_number"), table_name="teacher_payments")
    op.drop_index(op.f("ix_teacher_payments_contract_id"), table_name="teacher_payments")
    op.drop_table("teacher_payments")

    op.drop_index(op.f("ix_fee_structures_class_id"), table_name="fee_structures")
    op.drop_index(op.f("ix_fee_structures_academic_year_id"), table_name="fee_structures")
    op.drop_table("fee_structures")

    op.drop_index(op.f("ix_teacher_contracts_teacher_id"), table_name="teacher_contracts")
    op.drop_index(op.f("ix_teacher_contracts_academic_year_id"), table_name="teacher_contracts")
    op.drop_table("teacher_contracts")

    op.drop_index("idx_student_year", table_name="student_academic_records")
    op.drop_index(op.f("ix_student_academic_records_student_id"), table_name="student_academic_records")
    op.drop_index(op.f("ix_student_academic_records_section_id"), table_name="student_academic_records")
    op.drop_index(op.f("ix_student_academic_records_class_id"), table_name="student_academic_records")
    op.drop_index(op.f("ix_student_academic_records_academic_year_id"), table_name="student_academic_records")
    op.drop_table("student_academic_records")

    op.drop_index(op.f("ix_teacher_class_assignments_class_id"), table_name="teacher_class_assignments")
    op.drop_index(op.f("ix_teacher_class_assignments_teacher_id"), table_name="teacher_class_assignments")
    op.drop_table("teacher_class_assignments")

    op.drop_index(op.f("ix_students_student_id"), table_name="students")
    op.drop_index(op.f("ix_students_status"), table_name="students")
    op.drop_table("students")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_sections_class_id"), table_name="sections")
    op.drop_table("sections")

    op.drop_table("teachers")
    op.drop_table("classes")
    op.drop_table("academic_years")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")

    fee_type_enum.drop(op.get_bind(), checkfirst=False)
    payment_mode_enum.drop(op.get_bind(), checkfirst=False)
    attendance_status_enum.drop(op.get_bind(), checkfirst=False)
    student_status_enum.drop(op.get_bind(), checkfirst=False)
    role_enum.drop(op.get_bind(), checkfirst=False)
