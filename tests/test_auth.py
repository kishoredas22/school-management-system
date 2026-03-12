"""Authentication and RBAC tests."""

from tests.conftest import auth_headers


def test_login_returns_access_token(client):
    response = client.post("/api/v1/auth/login", json={"username": "superadmin", "password": "password123"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["token_type"] == "bearer"


def test_teacher_cannot_access_fee_report(client):
    response = client.get("/api/v1/reports/fees", headers=auth_headers(client, "teacher"))
    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_email_link_account_blocks_password_login_and_consumes_login_link(client):
    create_response = client.post(
        "/api/v1/users",
        headers=auth_headers(client, "superadmin"),
        json={
            "username": "email_admin",
            "email": "email.admin@example.com",
            "login_mode": "EMAIL_LINK",
            "role": "ADMIN",
            "active": True,
            "teacher_id": None,
            "password": None,
            "permissions": ["STUDENT_RECORDS", "REPORT_VIEW"],
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()["data"]
    assert payload["user"]["login_mode"] == "EMAIL_LINK"
    assert payload["email_link"]["login_url"]

    password_response = client.post(
        "/api/v1/auth/login",
        json={"username": "email_admin", "password": "password123"},
    )
    assert password_response.status_code == 401

    token = payload["email_link"]["login_url"].split("email_token=", 1)[1]
    email_response = client.post("/api/v1/auth/email-link/consume", json={"token": token})
    assert email_response.status_code == 200
    assert email_response.json()["data"]["login_mode"] == "EMAIL_LINK"
    assert "REPORT_VIEW" in email_response.json()["data"]["permissions"]


def test_admin_with_limited_permissions_cannot_open_fee_report(client):
    create_response = client.post(
        "/api/v1/users",
        headers=auth_headers(client, "superadmin"),
        json={
            "username": "restricted_admin",
            "password": "Restricted123",
            "email": None,
            "login_mode": "PASSWORD",
            "role": "ADMIN",
            "active": True,
            "teacher_id": None,
            "permissions": ["STUDENT_RECORDS"],
        },
    )

    assert create_response.status_code == 200

    restricted_login = client.post(
        "/api/v1/auth/login",
        json={"username": "restricted_admin", "password": "Restricted123"},
    )
    token = restricted_login.json()["data"]["access_token"]

    response = client.get("/api/v1/reports/fees", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
