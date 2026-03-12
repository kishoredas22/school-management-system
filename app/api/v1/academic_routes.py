"""Academic management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import ExamStatus, PermissionCode, RoleName
from app.repositories.academic_repository import AcademicRepository
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.academic_schema import (
    AdvancedPromotionRequest,
    ExamCreate,
    ExamStatusUpdate,
    GradeRuleCreate,
    StudentMarkBatchCreate,
    SubjectCreate,
    SubjectUpdate,
    TeacherSubjectAssignmentCreate,
    TimetableEntryCreate,
)
from app.services.academic_service import AcademicService
from app.services.promotion_service import PromotionService
from app.utils.helpers import success_response
from app.utils.receipt_generator import generate_report_card

router = APIRouter(prefix="/academics", tags=["academics"])


def _academic_service(db):
    return AcademicService(
        AcademicRepository(db),
        ReferenceRepository(db),
        AcademicYearRepository(db),
        TeacherRepository(db),
        StudentRepository(db),
    )


def _serialize_subject(item):
    return {
        "id": item.id,
        "name": item.name,
        "code": item.code,
        "is_active": item.is_active,
    }


def _serialize_teacher_subject(item):
    return {
        "id": item.id,
        "teacher_id": item.teacher_id,
        "teacher_name": item.teacher.name,
        "subject_id": item.subject_id,
        "subject_name": item.subject.name,
        "academic_year_id": item.academic_year_id,
        "academic_year_name": item.academic_year.name,
        "class_id": item.class_id,
        "class_name": item.class_room.name,
        "section_id": item.section_id,
        "section_name": item.section.name if item.section else None,
    }


def _serialize_timetable(item):
    return {
        "id": item.id,
        "academic_year_id": item.academic_year_id,
        "academic_year_name": item.academic_year.name,
        "class_id": item.class_id,
        "class_name": item.class_room.name,
        "section_id": item.section_id,
        "section_name": item.section.name if item.section else None,
        "subject_id": item.subject_id,
        "subject_name": item.subject.name,
        "teacher_id": item.teacher_id,
        "teacher_name": item.teacher.name,
        "weekday": item.weekday,
        "period_label": item.period_label,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "room_label": item.room_label,
    }


def _serialize_grade_rule(item):
    return {
        "id": item.id,
        "academic_year_id": item.academic_year_id,
        "academic_year_name": item.academic_year.name,
        "grade_label": item.grade_label,
        "min_percentage": item.min_percentage,
        "max_percentage": item.max_percentage,
        "remark": item.remark,
        "sort_order": item.sort_order,
    }


def _serialize_exam(item):
    return {
        "id": item.id,
        "academic_year_id": item.academic_year_id,
        "academic_year_name": item.academic_year.name,
        "class_id": item.class_id,
        "class_name": item.class_room.name,
        "section_id": item.section_id,
        "section_name": item.section.name if item.section else None,
        "name": item.name,
        "term_label": item.term_label,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "status": item.status,
        "subject_count": len(item.subjects),
        "subjects": [
            {
                "id": subject.id,
                "subject_id": subject.subject_id,
                "subject_name": subject.subject.name,
                "max_marks": subject.max_marks,
                "pass_marks": subject.pass_marks,
            }
            for subject in item.subjects
        ],
    }


@router.get("/subjects")
def list_subjects(
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    items = _academic_service(db).list_subjects()
    return success_response(data=[_serialize_subject(item) for item in items], message="Subjects retrieved")


@router.post("/subjects")
def create_subject(
    payload: SubjectCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).create_subject(payload, actor_id=current_user.id)
    return success_response(data=_serialize_subject(item), message="Subject created")


@router.put("/subjects/{subject_id}")
def update_subject(
    subject_id: UUID,
    payload: SubjectUpdate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).update_subject(str(subject_id), payload, actor_id=current_user.id)
    return success_response(data=_serialize_subject(item), message="Subject updated")


@router.get("/teacher-subjects")
def list_teacher_subject_assignments(
    year_id: UUID | None = None,
    class_id: UUID | None = None,
    teacher_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    items = _academic_service(db).list_teacher_subject_assignments(
        academic_year_id=str(year_id) if year_id else None,
        class_id=str(class_id) if class_id else None,
        teacher_id=str(teacher_id) if teacher_id else None,
    )
    return success_response(data=[_serialize_teacher_subject(item) for item in items], message="Teacher subject mappings retrieved")


@router.post("/teacher-subjects")
def create_teacher_subject_assignment(
    payload: TeacherSubjectAssignmentCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).create_teacher_subject_assignment(payload, actor_id=current_user.id)
    return success_response(data=_serialize_teacher_subject(item), message="Teacher subject mapping created")


@router.get("/timetable")
def list_timetable_entries(
    year_id: UUID | None = None,
    class_id: UUID | None = None,
    section_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    items = _academic_service(db).list_timetable_entries(
        academic_year_id=str(year_id) if year_id else None,
        class_id=str(class_id) if class_id else None,
        section_id=str(section_id) if section_id else None,
    )
    return success_response(data=[_serialize_timetable(item) for item in items], message="Timetable entries retrieved")


@router.post("/timetable")
def create_timetable_entry(
    payload: TimetableEntryCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).create_timetable_entry(payload, actor_id=current_user.id)
    return success_response(data=_serialize_timetable(item), message="Timetable entry created")


@router.get("/grade-rules")
def list_grade_rules(
    year_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    items = _academic_service(db).list_grade_rules(academic_year_id=str(year_id) if year_id else None)
    return success_response(data=[_serialize_grade_rule(item) for item in items], message="Grade rules retrieved")


@router.post("/grade-rules")
def create_grade_rule(
    payload: GradeRuleCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).create_grade_rule(payload, actor_id=current_user.id)
    return success_response(data=_serialize_grade_rule(item), message="Grade rule created")


@router.get("/exams")
def list_exams(
    year_id: UUID | None = None,
    class_id: UUID | None = None,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    items = _academic_service(db).list_exams(
        academic_year_id=str(year_id) if year_id else None,
        class_id=str(class_id) if class_id else None,
    )
    return success_response(data=[_serialize_exam(item) for item in items], message="Exams retrieved")


@router.post("/exams")
def create_exam(
    payload: ExamCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).create_exam(payload, actor_id=current_user.id)
    return success_response(data=_serialize_exam(item), message="Exam created")


@router.put("/exams/{exam_id}/status")
def update_exam_status(
    exam_id: UUID,
    payload: ExamStatusUpdate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    item = _academic_service(db).update_exam_status(str(exam_id), status=payload.status, actor_id=current_user.id)
    return success_response(data=_serialize_exam(item), message="Exam status updated")


@router.get("/exam-subjects/{exam_subject_id}/marks")
def get_marks_register(
    exam_subject_id: UUID,
    q: str | None = Query(default=None),
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    rows = _academic_service(db).get_marks_register(exam_subject_id=str(exam_subject_id), search=q)
    return success_response(data=rows, message="Marks register retrieved")


@router.post("/exam-subjects/{exam_subject_id}/marks")
def save_marks(
    exam_subject_id: UUID,
    payload: StudentMarkBatchCreate,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.REFERENCE_MANAGE)),
    db=Depends(get_db),
):
    result = _academic_service(db).save_marks(
        exam_subject_id=str(exam_subject_id),
        entries=payload.entries,
        actor_id=current_user.id,
    )
    return success_response(data=result, message="Marks saved")


@router.get("/exams/{exam_id}/results")
def list_exam_results(
    exam_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    data = _academic_service(db).list_exam_results(exam_id=str(exam_id))
    return success_response(data=data, message="Exam results retrieved")


@router.get("/report-cards/{exam_id}/{student_id}")
def get_report_card(
    exam_id: UUID,
    student_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    data = _academic_service(db).build_report_card(exam_id=str(exam_id), student_id=str(student_id))
    return success_response(data=data, message="Report card retrieved")


@router.get("/report-cards/{exam_id}/{student_id}/pdf")
def get_report_card_pdf(
    exam_id: UUID,
    student_id: UUID,
    _=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    __=Depends(require_permissions(PermissionCode.REPORT_VIEW)),
    db=Depends(get_db),
):
    payload = _academic_service(db).build_report_card(exam_id=str(exam_id), student_id=str(student_id))
    pdf = generate_report_card(payload)
    return Response(content=pdf, media_type="application/pdf")


@router.post("/promotions")
def run_year_end_promotion(
    payload: AdvancedPromotionRequest,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)),
    _=Depends(require_permissions(PermissionCode.STUDENT_STATUS)),
    db=Depends(get_db),
):
    result = PromotionService(
        StudentRepository(db),
        AcademicYearRepository(db),
        ReferenceRepository(db),
    ).promote_students_advanced(
        payload,
        actor_id=current_user.id,
    )
    return success_response(data=result, message="Advanced promotion workflow completed")
