"""Authentication endpoints."""

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.schemas.auth_schema import EmailLinkConsumeRequest, EmailLinkRequest, LoginRequest
from app.services.auth_service import AuthService
from app.utils.helpers import success_response
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db=Depends(get_db)):
    service = AuthService(UserRepository(db))
    data = service.login(username=payload.username, password=payload.password)
    return success_response(data=data)


@router.post("/email-link/request")
def request_email_link(payload: EmailLinkRequest, db=Depends(get_db)):
    service = AuthService(UserRepository(db))
    data = service.request_email_login_link(email=payload.email)
    return success_response(data=data, message="Email login link prepared")


@router.post("/email-link/consume")
def consume_email_link(payload: EmailLinkConsumeRequest, db=Depends(get_db)):
    service = AuthService(UserRepository(db))
    data = service.consume_email_login_link(token=payload.token)
    return success_response(data=data, message="Email login successful")


@router.post("/logout")
def logout():
    return success_response(message="Logout successful", data=None)
