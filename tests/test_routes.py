"""Regression tests for route behavior and serialization."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.reference import ClassRoom, Section
from tests.conftest import auth_headers


def test_reference_routes_are_available(client):
    classes_response = client.get("/api/v1/reference/classes", headers=auth_headers(client, "admin"))
    sections_response = client.get("/api/v1/reference/sections", headers=auth_headers(client, "admin"))

    assert classes_response.status_code == 200
    assert classes_response.json()["message"] == "Classes retrieved"
    assert sections_response.status_code == 200
    assert sections_response.json()["message"] == "Sections retrieved"


def test_paginated_routes_serialize_without_runtime_error(client):
    student_response = client.get(
        "/api/v1/students?page=1&size=5&include_inactive=true",
        headers=auth_headers(client, "admin"),
    )
    user_response = client.get("/api/v1/users?page=1&size=5", headers=auth_headers(client, "superadmin"))
    audit_response = client.get("/api/v1/audit-logs?page=1&size=5", headers=auth_headers(client, "superadmin"))

    assert student_response.status_code == 200
    assert student_response.json()["data"]["page"] == 1

    assert user_response.status_code == 200
    assert user_response.json()["data"]["total_records"] >= 1

    assert audit_response.status_code == 200
    assert "data" in audit_response.json()["data"]


def test_teacher_contracts_static_route_takes_precedence(client):
    response = client.get("/api/v1/teachers/contracts", headers=auth_headers(client, "admin"))

    assert response.status_code == 200
    assert response.json()["message"] == "Teacher contracts retrieved"


def test_academic_year_list_is_available_to_non_admin_operational_roles(client):
    teacher_response = client.get("/api/v1/academic-years", headers=auth_headers(client, "teacher"))
    data_entry_response = client.get("/api/v1/academic-years", headers=auth_headers(client, "data_entry"))

    assert teacher_response.status_code == 200
    assert teacher_response.json()["message"] == "Academic years retrieved"
    assert data_entry_response.status_code == 200
    assert data_entry_response.json()["message"] == "Academic years retrieved"


def test_teacher_contract_yearly_amount_auto_derives_monthly_salary(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))

    teacher_response = client.post(
        "/api/v1/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "name": "Nandita Roy",
            "phone": "9998887776",
            "assigned_classes": [],
        },
    )
    teacher_id = teacher_response.json()["data"]["id"]

    contract_response = client.post(
        "/api/v1/teachers/contracts",
        headers=auth_headers(client, "admin"),
        json={
            "teacher_id": teacher_id,
            "academic_year_id": str(year.id),
            "yearly_contract_amount": 120000,
            "monthly_salary": None,
        },
    )

    assert contract_response.status_code == 200

    list_response = client.get(
        f"/api/v1/teachers/contracts?teacher_id={teacher_id}",
        headers=auth_headers(client, "admin"),
    )
    contract = list_response.json()["data"][0]
    assert Decimal(str(contract["monthly_salary"])) == Decimal("10000.00")


def test_attendance_register_supports_editing_and_teacher_daily_view(client, db_session):
    today = date.today().isoformat()
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))

    student_response = client.post(
        "/api/v1/students",
        headers=auth_headers(client, "admin"),
        json={
            "student_id": "STU-ATT-1",
            "first_name": "Arjun",
            "last_name": "Pal",
            "dob": "2015-02-20",
            "guardian_name": "Maya Pal",
            "guardian_phone": "9999990000",
            "class_id": str(class_room.id),
            "section_id": str(section.id),
            "academic_year_id": str(year.id),
        },
    )
    student_id = student_response.json()["data"]["id"]

    register_before = client.get(
        f"/api/v1/attendance/students?class_id={class_room.id}&section_id={section.id}&date={today}",
        headers=auth_headers(client, "admin"),
    )
    assert register_before.status_code == 200
    assert register_before.json()["data"][0]["status"] is None

    mark_student_response = client.post(
        "/api/v1/attendance/students",
        headers=auth_headers(client, "admin"),
        json={
            "class_id": str(class_room.id),
            "section_id": str(section.id),
            "date": today,
            "attendance": [{"student_id": student_id, "status": "ABSENT"}],
        },
    )
    assert mark_student_response.status_code == 200

    register_after = client.get(
        f"/api/v1/attendance/students?class_id={class_room.id}&section_id={section.id}&date={today}",
        headers=auth_headers(client, "admin"),
    )
    assert register_after.status_code == 200
    assert register_after.json()["data"][0]["status"] == "ABSENT"

    teacher_response = client.post(
        "/api/v1/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "name": "Ira Bose",
            "phone": "8887776665",
            "assigned_classes": [],
        },
    )
    teacher_id = teacher_response.json()["data"]["id"]

    mark_teacher_response = client.post(
        "/api/v1/attendance/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "teacher_id": teacher_id,
            "date": today,
            "status": "PRESENT",
            "note": "On duty",
        },
    )
    assert mark_teacher_response.status_code == 200

    teacher_daily_view = client.get(
        f"/api/v1/attendance/teachers?date={today}",
        headers=auth_headers(client, "admin"),
    )
    assert teacher_daily_view.status_code == 200
    assert teacher_daily_view.json()["data"][0]["teacher_id"] == teacher_id
