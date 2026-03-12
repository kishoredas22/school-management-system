"""Academic permissions and marks-register tests."""

from datetime import date

from sqlalchemy import select

from app.core.permissions import allowed_permissions_for_role
from app.core.security import hash_password
from app.models.academic import Exam, ExamSubject, Subject, TeacherSubjectAssignment
from app.models.academic_year import AcademicYear
from app.models.enums import LoginMode, RoleName, StudentStatus
from app.models.reference import ClassRoom, Section
from app.models.role import Role
from app.models.student import Student, StudentAcademicRecord
from app.models.teacher import Teacher, TeacherClassAssignment
from app.models.user import User
from app.models.user_permission_grant import UserPermissionGrant
from tests.conftest import auth_headers


def test_teacher_with_scope_can_load_and_save_marks(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))
    teacher_user = db_session.scalar(select(User).where(User.username == "teacher"))

    teacher = Teacher(
        name="Marks Teacher",
        is_active=True,
        assignments=[
            TeacherClassAssignment(
                class_id=class_room.id,
                section_id=section.id,
                academic_year_id=year.id,
            )
        ],
    )
    db_session.add(teacher)
    db_session.flush()
    teacher_user.teacher_id = teacher.id

    subject = Subject(name="Mathematics", code="MATH", is_active=True)
    db_session.add(subject)
    db_session.flush()

    db_session.add(
        TeacherSubjectAssignment(
            teacher_id=teacher.id,
            subject_id=subject.id,
            academic_year_id=year.id,
            class_id=class_room.id,
            section_id=section.id,
        )
    )

    student = Student(
        student_id="STU-001",
        first_name="Asha",
        last_name="Patel",
        dob=date(2014, 5, 10),
        status=StudentStatus.ACTIVE,
    )
    db_session.add(student)
    db_session.flush()
    db_session.add(
        StudentAcademicRecord(
            student_id=student.id,
            academic_year_id=year.id,
            class_id=class_room.id,
            section_id=section.id,
        )
    )

    exam = Exam(
        academic_year_id=year.id,
        class_id=class_room.id,
        section_id=section.id,
        name="Term 1",
        term_label="Term 1",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 10),
        status="DRAFT",
        subjects=[
            ExamSubject(
                subject_id=subject.id,
                max_marks=100,
                pass_marks=35,
            )
        ],
    )
    db_session.add(exam)
    db_session.commit()

    headers = auth_headers(client, "teacher")

    exams_response = client.get("/api/v1/academics/exams", headers=headers)
    assert exams_response.status_code == 200
    exams = exams_response.json()["data"]
    assert len(exams) == 1
    assert exams[0]["subjects"][0]["subject_name"] == "Mathematics"

    exam_subject_id = exams[0]["subjects"][0]["id"]
    register_response = client.get(f"/api/v1/academics/exam-subjects/{exam_subject_id}/marks", headers=headers)
    assert register_response.status_code == 200
    rows = register_response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["student_name"] == "Asha Patel"

    save_response = client.post(
        f"/api/v1/academics/exam-subjects/{exam_subject_id}/marks",
        headers=headers,
        json={
            "entries": [
                {
                    "student_id": student.id,
                    "marks_obtained": 88,
                    "is_absent": False,
                    "remark": "Strong work",
                }
            ]
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["data"]["processed_count"] == 1


def test_teacher_without_linked_scope_cannot_open_marks_register(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))
    teacher_role = db_session.scalar(select(Role).where(Role.name == RoleName.TEACHER.value))

    scoped_teacher = Teacher(
        name="Scoped Faculty",
        is_active=True,
        assignments=[
            TeacherClassAssignment(
                class_id=class_room.id,
                section_id=section.id,
                academic_year_id=year.id,
            )
        ],
    )
    db_session.add(scoped_teacher)
    db_session.flush()

    subject = Subject(name="Science", code="SCI", is_active=True)
    db_session.add(subject)
    db_session.flush()
    db_session.add(
        TeacherSubjectAssignment(
            teacher_id=scoped_teacher.id,
            subject_id=subject.id,
            academic_year_id=year.id,
            class_id=class_room.id,
            section_id=section.id,
        )
    )

    exam = Exam(
        academic_year_id=year.id,
        class_id=class_room.id,
        section_id=section.id,
        name="Unit Test",
        term_label="Unit Test",
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 2),
        status="DRAFT",
        subjects=[
            ExamSubject(
                subject_id=subject.id,
                max_marks=50,
                pass_marks=18,
            )
        ],
    )
    db_session.add(exam)
    db_session.flush()

    teacher_user = User(
        username="teacher_unscoped",
        password_hash=hash_password("password123"),
        login_mode=LoginMode.PASSWORD,
        role_id=teacher_role.id,
        is_active=True,
    )
    db_session.add(teacher_user)
    db_session.flush()
    db_session.add_all(
        [
            UserPermissionGrant(user_id=teacher_user.id, permission_code=permission)
            for permission in allowed_permissions_for_role(RoleName.TEACHER)
        ]
    )
    db_session.commit()

    login_response = client.post("/api/v1/auth/login", json={"username": "teacher_unscoped", "password": "password123"})
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam_subject_id = str(exam.subjects[0].id)
    register_response = client.get(f"/api/v1/academics/exam-subjects/{exam_subject_id}/marks", headers=headers)
    assert register_response.status_code == 403
    assert register_response.json()["error_code"] == "FORBIDDEN"
