"""Student workflow tests."""

from uuid import UUID

from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.reference import ClassRoom, Section
from app.models.student import Student
from tests.conftest import auth_headers


def test_create_student_and_update_status(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))

    create_response = client.post(
        "/api/v1/students",
        headers=auth_headers(client, "admin"),
        json={
            "first_name": "Rahul",
            "last_name": "Das",
            "dob": "2015-05-10",
            "guardian_name": "Suresh Das",
            "guardian_phone": "9876543210",
            "class_id": str(class_room.id),
            "section_id": str(section.id),
            "academic_year_id": str(year.id),
        },
    )
    assert create_response.status_code == 200
    student_id = create_response.json()["data"]["id"]

    status_response = client.put(
        f"/api/v1/students/{student_id}/status",
        headers=auth_headers(client, "admin"),
        json={"status": "INACTIVE"},
    )
    assert status_response.status_code == 200

    student = db_session.scalar(select(Student).where(Student.id == UUID(student_id)))
    assert student.status == "INACTIVE"
