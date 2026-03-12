"""Fee workflow tests."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.reference import ClassRoom, Section
from tests.conftest import auth_headers


def test_fee_payment_updates_summary(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))

    student_response = client.post(
        "/api/v1/students",
        headers=auth_headers(client, "admin"),
        json={
            "student_id": "STU-001",
            "first_name": "Asha",
            "last_name": "Sen",
            "dob": "2014-01-01",
            "guardian_name": "Rita Sen",
            "guardian_phone": "9999999999",
            "class_id": str(class_room.id),
            "section_id": str(section.id),
            "academic_year_id": str(year.id),
        },
    )
    student_id = student_response.json()["data"]["id"]

    fee_structure_response = client.post(
        "/api/v1/fees/structures",
        headers=auth_headers(client, "admin"),
        json={
            "class_id": str(class_room.id),
            "academic_year_id": str(year.id),
            "fee_name": "Tuition",
            "amount": 20000,
            "fee_type": "ONE_TIME",
        },
    )
    fee_structure_id = fee_structure_response.json()["data"]["id"]

    payment_response = client.post(
        "/api/v1/fees/payments",
        headers=auth_headers(client, "admin"),
        json={
            "student_id": student_id,
            "fee_structure_id": fee_structure_id,
            "amount": 5000,
            "payment_mode": "CASH",
            "payment_date": "2025-07-01",
        },
    )
    assert payment_response.status_code == 200

    summary_response = client.get(
        f"/api/v1/fees/payments/student/{student_id}",
        headers=auth_headers(client, "admin"),
    )
    data = summary_response.json()["data"]
    assert Decimal(str(data["total_fee"])) == Decimal("20000")
    assert Decimal(str(data["total_paid"])) == Decimal("5000")
    assert Decimal(str(data["pending"])) == Decimal("15000")
