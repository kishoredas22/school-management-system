"""Top-level API router."""

from fastapi import APIRouter

from app.api.v1.academic_routes import router as academic_router
from app.api.v1.academic_year_routes import router as academic_year_router
from app.api.v1.attendance_routes import router as attendance_router
from app.api.v1.audit_routes import router as audit_router
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.fee_routes import router as fee_router
from app.api.v1.reference_routes import router as reference_router
from app.api.v1.report_routes import router as report_router
from app.api.v1.student_routes import router as student_router
from app.api.v1.teacher_routes import router as teacher_router
from app.api.v1.user_routes import router as user_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(academic_router)
api_router.include_router(academic_year_router)
api_router.include_router(reference_router)
api_router.include_router(student_router)
api_router.include_router(attendance_router)
api_router.include_router(fee_router)
api_router.include_router(teacher_router)
api_router.include_router(report_router)
api_router.include_router(audit_router)
