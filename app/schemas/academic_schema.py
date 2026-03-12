"""Academic management schemas."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ExamStatus, PromotionAction


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=20)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class TeacherSubjectAssignmentCreate(BaseModel):
    teacher_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID | None = None


class TimetableEntryCreate(BaseModel):
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID | None = None
    subject_id: UUID
    teacher_id: UUID
    weekday: str = Field(min_length=3, max_length=12)
    period_label: str = Field(min_length=1, max_length=40)
    start_time: time
    end_time: time
    room_label: str | None = Field(default=None, max_length=40)


class GradeRuleCreate(BaseModel):
    academic_year_id: UUID
    grade_label: str = Field(min_length=1, max_length=20)
    min_percentage: Decimal
    max_percentage: Decimal
    remark: str | None = Field(default=None, max_length=150)
    sort_order: int = 0

    @field_validator("grade_label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip().upper()


class ExamSubjectCreate(BaseModel):
    subject_id: UUID
    max_marks: Decimal
    pass_marks: Decimal


class ExamCreate(BaseModel):
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    term_label: str | None = Field(default=None, max_length=50)
    start_date: date
    end_date: date
    subjects: list[ExamSubjectCreate] = Field(default_factory=list)


class ExamStatusUpdate(BaseModel):
    status: ExamStatus


class StudentMarkEntry(BaseModel):
    student_id: UUID
    marks_obtained: Decimal | None = None
    is_absent: bool = False
    remark: str | None = Field(default=None, max_length=300)


class StudentMarkBatchCreate(BaseModel):
    entries: list[StudentMarkEntry] = Field(default_factory=list)


class PromotionDecisionItem(BaseModel):
    student_id: UUID
    action: PromotionAction = PromotionAction.PROMOTE
    target_class_id: UUID | None = None
    target_section_id: UUID | None = None
    remark: str | None = Field(default=None, max_length=200)


class AdvancedPromotionRequest(BaseModel):
    academic_year_from: UUID
    academic_year_to: UUID
    default_action: PromotionAction = PromotionAction.PROMOTE
    default_target_class_id: UUID | None = None
    default_target_section_id: UUID | None = None
    student_ids: list[UUID] = Field(default_factory=list)
    decisions: list[PromotionDecisionItem] = Field(default_factory=list)


class SubjectRead(BaseModel):
    id: UUID
    name: str
    code: str
    is_active: bool


class TeacherSubjectAssignmentRead(BaseModel):
    id: UUID
    teacher_id: UUID
    teacher_name: str
    subject_id: UUID
    subject_name: str
    academic_year_id: UUID
    academic_year_name: str
    class_id: UUID
    class_name: str
    section_id: UUID | None = None
    section_name: str | None = None


class TimetableEntryRead(BaseModel):
    id: UUID
    academic_year_id: UUID
    academic_year_name: str
    class_id: UUID
    class_name: str
    section_id: UUID | None = None
    section_name: str | None = None
    subject_id: UUID
    subject_name: str
    teacher_id: UUID
    teacher_name: str
    weekday: str
    period_label: str
    start_time: time
    end_time: time
    room_label: str | None = None


class GradeRuleRead(BaseModel):
    id: UUID
    academic_year_id: UUID
    academic_year_name: str
    grade_label: str
    min_percentage: Decimal
    max_percentage: Decimal
    remark: str | None = None
    sort_order: int


class ExamSubjectRead(BaseModel):
    id: UUID
    subject_id: UUID
    subject_name: str
    max_marks: Decimal
    pass_marks: Decimal


class ExamRead(BaseModel):
    id: UUID
    academic_year_id: UUID
    academic_year_name: str
    class_id: UUID
    class_name: str
    section_id: UUID | None = None
    section_name: str | None = None
    name: str
    term_label: str | None = None
    start_date: date
    end_date: date
    status: str
    subject_count: int
    subjects: list[ExamSubjectRead]


class StudentMarkRegisterRow(BaseModel):
    student_id: UUID
    student_name: str
    student_code: str | None = None
    marks_obtained: Decimal | None = None
    is_absent: bool
    remark: str | None = None


class ReportCardSubjectRow(BaseModel):
    subject_name: str
    max_marks: Decimal
    pass_marks: Decimal
    marks_obtained: Decimal | None = None
    is_absent: bool
    result: str


class ReportCardRead(BaseModel):
    exam_id: UUID
    exam_name: str
    term_label: str | None = None
    academic_year_name: str
    class_name: str
    section_name: str | None = None
    student_id: UUID
    student_name: str
    student_code: str | None = None
    generated_at: datetime
    total_marks: Decimal
    obtained_marks: Decimal
    percentage: Decimal
    overall_grade: str | None = None
    overall_remark: str | None = None
    result: str
    subject_rows: list[ReportCardSubjectRow]
