"""Add academic management tables."""

from alembic import op
import sqlalchemy as sa


revision = "0005_academic_mgmt"
down_revision = "0004_perm_code_expand"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_subjects_code"), "subjects", ["code"], unique=True)

    op.create_table(
        "teacher_subject_assignments",
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "class_id", "section_id", "subject_id", name="uq_teacher_subject_scope"),
    )
    op.create_index(op.f("ix_teacher_subject_assignments_teacher_id"), "teacher_subject_assignments", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_teacher_subject_assignments_subject_id"), "teacher_subject_assignments", ["subject_id"], unique=False)
    op.create_index(op.f("ix_teacher_subject_assignments_academic_year_id"), "teacher_subject_assignments", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_teacher_subject_assignments_class_id"), "teacher_subject_assignments", ["class_id"], unique=False)

    op.create_table(
        "timetable_entries",
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.String(length=12), nullable=False),
        sa.Column("period_label", sa.String(length=40), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("room_label", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "class_id", "section_id", "weekday", "period_label", name="uq_timetable_scope_slot"),
    )
    op.create_index(op.f("ix_timetable_entries_academic_year_id"), "timetable_entries", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_class_id"), "timetable_entries", ["class_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_subject_id"), "timetable_entries", ["subject_id"], unique=False)
    op.create_index(op.f("ix_timetable_entries_teacher_id"), "timetable_entries", ["teacher_id"], unique=False)

    op.create_table(
        "grade_rules",
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("grade_label", sa.String(length=20), nullable=False),
        sa.Column("min_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("remark", sa.String(length=150), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "grade_label", name="uq_grade_rule_year_label"),
    )
    op.create_index(op.f("ix_grade_rules_academic_year_id"), "grade_rules", ["academic_year_id"], unique=False)

    op.create_table(
        "exams",
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("term_label", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exams_academic_year_id"), "exams", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_exams_class_id"), "exams", ["class_id"], unique=False)

    op.create_table(
        "exam_subjects",
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("max_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("pass_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),
    )
    op.create_index(op.f("ix_exam_subjects_exam_id"), "exam_subjects", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_subjects_subject_id"), "exam_subjects", ["subject_id"], unique=False)

    op.create_table(
        "student_marks",
        sa.Column("exam_subject_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_absent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["exam_subject_id"], ["exam_subjects.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_subject_id", "student_id", name="uq_exam_subject_student_mark"),
    )
    op.create_index(op.f("ix_student_marks_exam_subject_id"), "student_marks", ["exam_subject_id"], unique=False)
    op.create_index(op.f("ix_student_marks_student_id"), "student_marks", ["student_id"], unique=False)

    op.alter_column("subjects", "is_active", server_default=None)
    op.alter_column("grade_rules", "sort_order", server_default=None)
    op.alter_column("exams", "status", server_default=None)
    op.alter_column("student_marks", "is_absent", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_student_marks_student_id"), table_name="student_marks")
    op.drop_index(op.f("ix_student_marks_exam_subject_id"), table_name="student_marks")
    op.drop_table("student_marks")

    op.drop_index(op.f("ix_exam_subjects_subject_id"), table_name="exam_subjects")
    op.drop_index(op.f("ix_exam_subjects_exam_id"), table_name="exam_subjects")
    op.drop_table("exam_subjects")

    op.drop_index(op.f("ix_exams_class_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_academic_year_id"), table_name="exams")
    op.drop_table("exams")

    op.drop_index(op.f("ix_grade_rules_academic_year_id"), table_name="grade_rules")
    op.drop_table("grade_rules")

    op.drop_index(op.f("ix_timetable_entries_teacher_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_subject_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_class_id"), table_name="timetable_entries")
    op.drop_index(op.f("ix_timetable_entries_academic_year_id"), table_name="timetable_entries")
    op.drop_table("timetable_entries")

    op.drop_index(op.f("ix_teacher_subject_assignments_class_id"), table_name="teacher_subject_assignments")
    op.drop_index(op.f("ix_teacher_subject_assignments_academic_year_id"), table_name="teacher_subject_assignments")
    op.drop_index(op.f("ix_teacher_subject_assignments_subject_id"), table_name="teacher_subject_assignments")
    op.drop_index(op.f("ix_teacher_subject_assignments_teacher_id"), table_name="teacher_subject_assignments")
    op.drop_table("teacher_subject_assignments")

    op.drop_index(op.f("ix_subjects_code"), table_name="subjects")
    op.drop_table("subjects")
