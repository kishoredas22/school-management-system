"""Teacher salary slip and payroll tests."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.attendance import TeacherAttendance
from app.models.enums import AttendanceStatus, PaymentMode
from app.models.teacher import TeacherPayment
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.teacher_service import TeacherService
from tests.conftest import auth_headers


def test_salary_slip_payload_includes_attendance_and_year_to_date_totals(client, db_session):
    year = db_session.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))

    teacher_response = client.post(
        "/api/v1/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "name": "Bikash Nayak",
            "phone": "9990001112",
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
    assert contract_response.status_code == 200

    contract_id = client.get(
        f"/api/v1/teachers/contracts?teacher_id={teacher_id}",
        headers=auth_headers(client, "admin"),
    ).json()["data"][0]["id"]

    db_session.add_all(
        [
            TeacherAttendance(
                teacher_id=teacher_id,
                academic_year_id=year.id,
                attendance_date=date(2026, 3, 1),
                status=AttendanceStatus.PRESENT,
                note="On duty",
            ),
            TeacherAttendance(
                teacher_id=teacher_id,
                academic_year_id=year.id,
                attendance_date=date(2026, 3, 2),
                status=AttendanceStatus.PRESENT,
                note="On duty",
            ),
            TeacherAttendance(
                teacher_id=teacher_id,
                academic_year_id=year.id,
                attendance_date=date(2026, 3, 3),
                status=AttendanceStatus.ABSENT,
                note="Absent",
            ),
            TeacherPayment(
                teacher_id=teacher_id,
                contract_id=contract_id,
                amount_paid=Decimal("4000.00"),
                payment_mode=PaymentMode.BANK,
                payment_date=date(2025, 12, 20),
                receipt_number="SAL-OLD-DEC",
            ),
            TeacherPayment(
                teacher_id=teacher_id,
                contract_id=contract_id,
                amount_paid=Decimal("3000.00"),
                payment_mode=PaymentMode.BANK,
                payment_date=date(2026, 3, 5),
                receipt_number="SAL-MAR-001",
            ),
            TeacherPayment(
                teacher_id=teacher_id,
                contract_id=contract_id,
                amount_paid=Decimal("4500.00"),
                payment_mode=PaymentMode.UPI,
                payment_date=date(2026, 3, 18),
                receipt_number="SAL-MAR-002",
            ),
        ]
    )
    db_session.commit()

    service = TeacherService(
        TeacherRepository(db_session),
        ReferenceRepository(db_session),
        AcademicYearRepository(db_session),
        AttendanceRepository(db_session),
    )
    payment = db_session.scalar(select(TeacherPayment).where(TeacherPayment.receipt_number == "SAL-MAR-002"))
    payload = service.build_salary_slip_payload(payment.id)

    assert payload["teacher_name"] == "Bikash Nayak"
    assert payload["salary_month"] == "March 2026"
    assert payload["teacher_phone"] == "9990001112"
    assert payload["days_worked"] == 2
    assert payload["total_days_in_month"] == 31
    assert Decimal(payload["monthly_salary"]) == Decimal("10000.00")
    assert Decimal(payload["contract_total"]) == Decimal("120000.00")
    assert Decimal(payload["paid_for_month"]) == Decimal("7500.00")
    assert Decimal(payload["paid_year_to_date"]) == Decimal("11500.00")
    assert Decimal(payload["remaining_balance"]) == Decimal("108500.00")


def test_salary_slip_route_returns_pdf(client):
    year_response = client.get("/api/v1/academic-years", headers=auth_headers(client, "admin"))
    year_id = year_response.json()["data"][0]["id"]

    teacher_response = client.post(
        "/api/v1/teachers",
        headers=auth_headers(client, "admin"),
        json={
            "name": "Aparna Das",
            "phone": "9876543211",
            "assigned_classes": [],
        },
    )
    teacher_id = teacher_response.json()["data"]["id"]

    contract_response = client.post(
        "/api/v1/teachers/contracts",
        headers=auth_headers(client, "admin"),
        json={
            "teacher_id": teacher_id,
            "academic_year_id": year_id,
            "yearly_contract_amount": 96000,
            "monthly_salary": 8000,
        },
    )
    assert contract_response.status_code == 200

    contract_id = client.get(
        f"/api/v1/teachers/contracts?teacher_id={teacher_id}",
        headers=auth_headers(client, "admin"),
    ).json()["data"][0]["id"]

    payment_response = client.post(
        "/api/v1/teachers/payments",
        headers=auth_headers(client, "admin"),
        json={
            "teacher_id": teacher_id,
            "contract_id": contract_id,
            "amount": 8000,
            "payment_mode": "BANK",
            "payment_date": "2026-03-10",
        },
    )
    payment_id = payment_response.json()["data"]["id"]

    slip_response = client.get(
        f"/api/v1/teachers/payments/{payment_id}/slip",
        headers=auth_headers(client, "admin"),
    )

    assert slip_response.status_code == 200
    assert slip_response.headers["content-type"] == "application/pdf"
    assert len(slip_response.content) > 1000
