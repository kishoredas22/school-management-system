"""Permission catalog and role defaults."""

from dataclasses import dataclass

from app.models.enums import PermissionCode, RoleName


@dataclass(frozen=True)
class PermissionDefinition:
    code: PermissionCode
    label: str
    description: str
    group: str
    visible: bool = True


PERMISSION_DEFINITIONS: tuple[PermissionDefinition, ...] = (
    PermissionDefinition(
        code=PermissionCode.USER_MANAGE,
        label="User access",
        description="Create, edit, and review staff accounts from the backoffice.",
        group="Identity",
    ),
    PermissionDefinition(
        code=PermissionCode.TEACHER_VIEW,
        label="Teacher directory",
        description="View teacher profiles and classroom allocations.",
        group="Faculty",
    ),
    PermissionDefinition(
        code=PermissionCode.TEACHER_MANAGE,
        label="Teacher records",
        description="Create and update teacher profiles, contracts, payroll, and salary slips.",
        group="Faculty",
    ),
    PermissionDefinition(
        code=PermissionCode.TEACHER_SCOPE_MANAGE,
        label="Teacher class scope",
        description="Manage class, section, and academic-year scope assigned to teacher profiles.",
        group="Faculty",
    ),
    PermissionDefinition(
        code=PermissionCode.STUDENT_VIEW,
        label="Student roster",
        description="View and search student records across the ERP.",
        group="Students",
    ),
    PermissionDefinition(
        code=PermissionCode.STUDENT_MANAGE,
        label="Student records",
        description="Create and update student master records and placement.",
        group="Students",
    ),
    PermissionDefinition(
        code=PermissionCode.STUDENT_STATUS,
        label="Student status",
        description="Change student lifecycle status and run promotion workflows.",
        group="Students",
    ),
    PermissionDefinition(
        code=PermissionCode.ATTENDANCE_STUDENT,
        label="Student attendance",
        description="Load and submit student attendance registers.",
        group="Attendance",
    ),
    PermissionDefinition(
        code=PermissionCode.ATTENDANCE_TEACHER,
        label="Teacher attendance",
        description="Record and review teacher attendance.",
        group="Attendance",
    ),
    PermissionDefinition(
        code=PermissionCode.FEE_VIEW,
        label="Fee summaries",
        description="View fee structures, student fee summaries, and receipts.",
        group="Finance",
    ),
    PermissionDefinition(
        code=PermissionCode.FEE_MANAGE,
        label="Fee operations",
        description="Create fee structures and record fee payments.",
        group="Finance",
    ),
    PermissionDefinition(
        code=PermissionCode.REPORT_VIEW,
        label="Reports",
        description="View finance, attendance, and payroll reports.",
        group="Reporting",
    ),
    PermissionDefinition(
        code=PermissionCode.SUBJECT_MANAGE,
        label="Subject master",
        description="Create and maintain the school subject catalog.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.TEACHER_SUBJECT_MANAGE,
        label="Teacher-subject mapping",
        description="Map teachers to subjects by academic year, class, and section.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.EXAM_MANAGE,
        label="Exam setup",
        description="Create, review, and publish exam definitions.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.MARKS_ENTRY,
        label="Marks entry",
        description="Open marks registers and submit subject-wise student marks.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.GRADE_RULE_MANAGE,
        label="Grade rules",
        description="Maintain percentage bands, grade labels, and academic remarks.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.TIMETABLE_MANAGE,
        label="Timetable",
        description="Create and review class and section timetable entries.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.REPORT_CARD_VIEW,
        label="Report cards",
        description="Review exam results and generate printable report cards.",
        group="Academics",
    ),
    PermissionDefinition(
        code=PermissionCode.AUDIT_VIEW,
        label="Audit logs",
        description="View audit-trail history and change events.",
        group="Governance",
    ),
    PermissionDefinition(
        code=PermissionCode.REFERENCE_MANAGE,
        label="Class and section setup",
        description="Create and manage classes and sections used across the ERP.",
        group="Configuration",
    ),
    PermissionDefinition(
        code=PermissionCode.ACADEMIC_YEAR_MANAGE,
        label="Academic year control",
        description="Create, activate, and close academic years.",
        group="Configuration",
    ),
    PermissionDefinition(
        code=PermissionCode.STUDENT_RECORDS,
        label="Legacy student records",
        description="Backward-compatible permission kept for older accounts.",
        group="Legacy",
        visible=False,
    ),
)


ROLE_PERMISSION_DEFAULTS: dict[RoleName, tuple[PermissionCode, ...]] = {
    RoleName.SUPER_ADMIN: tuple(item.code for item in PERMISSION_DEFINITIONS if item.visible)
    + (PermissionCode.STUDENT_RECORDS,),
    RoleName.ADMIN: (
        PermissionCode.TEACHER_VIEW,
        PermissionCode.TEACHER_MANAGE,
        PermissionCode.TEACHER_SCOPE_MANAGE,
        PermissionCode.STUDENT_VIEW,
        PermissionCode.STUDENT_MANAGE,
        PermissionCode.STUDENT_STATUS,
        PermissionCode.ATTENDANCE_STUDENT,
        PermissionCode.ATTENDANCE_TEACHER,
        PermissionCode.FEE_VIEW,
        PermissionCode.FEE_MANAGE,
        PermissionCode.REPORT_VIEW,
        PermissionCode.SUBJECT_MANAGE,
        PermissionCode.TEACHER_SUBJECT_MANAGE,
        PermissionCode.EXAM_MANAGE,
        PermissionCode.MARKS_ENTRY,
        PermissionCode.GRADE_RULE_MANAGE,
        PermissionCode.TIMETABLE_MANAGE,
        PermissionCode.REPORT_CARD_VIEW,
        PermissionCode.REFERENCE_MANAGE,
    ),
    RoleName.DATA_ENTRY: (
        PermissionCode.TEACHER_VIEW,
        PermissionCode.STUDENT_VIEW,
        PermissionCode.STUDENT_MANAGE,
        PermissionCode.ATTENDANCE_STUDENT,
        PermissionCode.ATTENDANCE_TEACHER,
        PermissionCode.FEE_VIEW,
        PermissionCode.FEE_MANAGE,
    ),
    RoleName.TEACHER: (
        PermissionCode.STUDENT_VIEW,
        PermissionCode.ATTENDANCE_STUDENT,
        PermissionCode.MARKS_ENTRY,
    ),
}


def allowed_permissions_for_role(role_name: RoleName) -> tuple[PermissionCode, ...]:
    return ROLE_PERMISSION_DEFAULTS.get(role_name, ())


def expand_permission_codes(permission_codes: set[str]) -> set[str]:
    """Expand implicit and legacy permission aliases into effective permissions."""

    expanded = set(permission_codes)
    if PermissionCode.STUDENT_RECORDS.value in expanded:
        expanded.update({PermissionCode.STUDENT_VIEW.value, PermissionCode.STUDENT_MANAGE.value})
    if PermissionCode.STUDENT_VIEW.value in expanded or PermissionCode.STUDENT_MANAGE.value in expanded:
        expanded.add(PermissionCode.STUDENT_RECORDS.value)
    if PermissionCode.STUDENT_MANAGE.value in expanded:
        expanded.add(PermissionCode.STUDENT_VIEW.value)
    if PermissionCode.TEACHER_MANAGE.value in expanded:
        expanded.add(PermissionCode.TEACHER_VIEW.value)
    if PermissionCode.FEE_MANAGE.value in expanded:
        expanded.add(PermissionCode.FEE_VIEW.value)
    return expanded


def effective_permissions_for_user(*, role_name: str, assigned_permissions: list[str]) -> set[str]:
    """Return the effective permission set for a user."""

    if role_name == RoleName.SUPER_ADMIN.value:
        return expand_permission_codes(
            {
                *(item.code.value for item in PERMISSION_DEFINITIONS if item.visible),
                PermissionCode.STUDENT_RECORDS.value,
            }
        )

    if assigned_permissions:
        return expand_permission_codes(set(assigned_permissions))

    try:
        role = RoleName(role_name)
    except ValueError:
        return set()
    return expand_permission_codes({permission.value for permission in allowed_permissions_for_role(role)})


def serialize_permission_catalog() -> list[dict[str, str]]:
    return [
        {
            "code": item.code.value,
            "label": item.label,
            "description": item.description,
            "group": item.group,
        }
        for item in PERMISSION_DEFINITIONS
        if item.visible
    ]


def serialize_role_defaults() -> dict[str, list[str]]:
    return {
        role.value: sorted(expand_permission_codes({item.value for item in permissions}))
        for role, permissions in ROLE_PERMISSION_DEFAULTS.items()
    }
