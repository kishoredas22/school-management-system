"""Tests for reporting exports and audit review workflows."""

from datetime import date

from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.reference import ClassRoom, Section
from tests.conftest import auth_headers


def test_reporting_dashboard_and_exports_are_available(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))
    class_room = db_session.scalar(select(ClassRoom).where(ClassRoom.name == "Class 1"))
    section = db_session.scalar(select(Section).where(Section.class_id == class_room.id))

    student_response = client.post(
        "/api/v1/students",
        headers=auth_headers(client, "admin"),
        json={
            "student_id": "STU-REP-1",
            "first_name": "Mira",
            "last_name": "Sen",
            "dob": "2015-04-11",
            "guardian_name": "Rita Sen",
            "guardian_phone": "9000000001",
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
            "fee_name": "Annual Fee",
            "amount": 1000,
            "fee_type": "ONE_TIME",
        },
    )
    structure_id = fee_structure_response.json()["data"]["id"]

    client.post(
        "/api/v1/fees/payments",
        headers=auth_headers(client, "admin"),
        json={
            "student_id": student_id,
            "fee_structure_id": structure_id,
            "amount": 400,
            "payment_mode": "CASH",
            "payment_date": date.today().isoformat(),
        },
    )

    teacher_response = client.post(
        "/api/v1/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "name": "Riya Bose",
            "phone": "9000000002",
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
            "monthly_salary": 10000,
        },
    )
    contract_id = contract_response.json()["data"]["id"]
    client.post(
        "/api/v1/teachers/payments",
        headers=auth_headers(client, "admin"),
        json={
            "teacher_id": teacher_id,
            "contract_id": contract_id,
            "amount": 10000,
            "payment_mode": "BANK",
            "payment_date": date.today().isoformat(),
        },
    )

    dashboard_response = client.get("/api/v1/reports/dashboard", headers=auth_headers(client, "admin"))
    trend_response = client.get(
        f"/api/v1/reports/finance/trend?calendar_year={date.today().year}",
        headers=auth_headers(client, "admin"),
    )
    status_response = client.get("/api/v1/reports/students/status", headers=auth_headers(client, "admin"))
    export_response = client.get(
        "/api/v1/reports/teacher-payments/export",
        headers=auth_headers(client, "admin"),
    )

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["data"]["student_total"] >= 1
    assert trend_response.status_code == 200
    assert len(trend_response.json()["data"]) == 12
    assert status_response.status_code == 200
    assert any(item["status"] == "ACTIVE" for item in status_response.json()["data"])
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "Teacher,Contract Total,Paid,Pending Balance" in export_response.text


def test_audit_filters_summary_and_review_flow(client):
    create_user_response = client.post(
        "/api/v1/users",
        headers=auth_headers(client, "superadmin"),
        json={
            "username": "governance-admin",
            "password": "password123",
            "email": None,
            "login_mode": "PASSWORD",
            "role": "ADMIN",
            "active": True,
            "teacher_id": None,
            "permissions": [
                "TEACHER_VIEW",
                "TEACHER_MANAGE",
                "TEACHER_SCOPE_MANAGE",
                "STUDENT_VIEW",
                "STUDENT_MANAGE",
                "STUDENT_STATUS",
                "ATTENDANCE_STUDENT",
                "ATTENDANCE_TEACHER",
                "FEE_VIEW",
                "FEE_MANAGE",
                "REPORT_VIEW",
                "REFERENCE_MANAGE",
            ],
        },
    )
    assert create_user_response.status_code == 200

    summary_response = client.get("/api/v1/audit-logs/summary", headers=auth_headers(client, "superadmin"))
    pending_response = client.get(
        "/api/v1/audit-logs?review_status=PENDING&page=1&size=10",
        headers=auth_headers(client, "superadmin"),
    )
    export_response = client.get(
        "/api/v1/audit-logs/export?review_status=PENDING",
        headers=auth_headers(client, "superadmin"),
    )

    assert summary_response.status_code == 200
    assert summary_response.json()["data"]["pending_reviews"] >= 1
    assert pending_response.status_code == 200
    assert pending_response.json()["data"]["total_records"] >= 1
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")

    audit_item = pending_response.json()["data"]["data"][0]
    review_response = client.post(
        f"/api/v1/audit-logs/{audit_item['id']}/review",
        headers=auth_headers(client, "superadmin"),
        json={
            "status": "APPROVED",
            "review_note": "Backoffice verified.",
        },
    )
    approved_response = client.get(
        "/api/v1/audit-logs?review_status=APPROVED&page=1&size=10",
        headers=auth_headers(client, "superadmin"),
    )

    assert review_response.status_code == 200
    assert review_response.json()["data"]["review_status"] == "APPROVED"
    assert review_response.json()["data"]["review_note"] == "Backoffice verified."
    assert approved_response.status_code == 200
    assert approved_response.json()["data"]["total_records"] >= 1
