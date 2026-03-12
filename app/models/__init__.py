"""ORM models."""

from app.models.academic_year import AcademicYear
from app.models.academic import Exam, ExamSubject, GradeRule, StudentMark, Subject, TeacherSubjectAssignment, TimetableEntry
from app.models.attendance import StudentAttendance, TeacherAttendance
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.email_login_token import EmailLoginToken
from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure
from app.models.reference import ClassRoom, Section
from app.models.role import Role
from app.models.student import Student, StudentAcademicRecord
from app.models.teacher import Teacher, TeacherClassAssignment, TeacherContract, TeacherPayment
from app.models.user import User
from app.models.user_permission_grant import UserPermissionGrant

__all__ = [
    "AcademicYear",
    "AuditLog",
    "Base",
    "ClassRoom",
    "EmailLoginToken",
    "Exam",
    "ExamSubject",
    "FeePayment",
    "FeeStructure",
    "GradeRule",
    "Role",
    "Section",
    "StudentMark",
    "Student",
    "StudentAcademicRecord",
    "StudentAttendance",
    "Subject",
    "Teacher",
    "TeacherAttendance",
    "TeacherClassAssignment",
    "TeacherContract",
    "TeacherPayment",
    "TeacherSubjectAssignment",
    "TimetableEntry",
    "User",
    "UserPermissionGrant",
]
