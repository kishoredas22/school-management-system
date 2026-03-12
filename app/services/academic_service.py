"""Academic management business logic."""

from decimal import Decimal

from app.core.exceptions import AuthorizationException, ConflictException, NotFoundException, ValidationException
from app.models.academic import Exam, ExamSubject, GradeRule, StudentMark, Subject, TeacherSubjectAssignment, TimetableEntry
from app.models.enums import ExamStatus
from app.repositories.academic_repository import AcademicRepository
from app.repositories.academic_year_repository import AcademicYearRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict, utcnow


class AcademicService:
    """Business logic for academic setup, marks, and report cards."""

    def __init__(
        self,
        academic_repository: AcademicRepository,
        reference_repository: ReferenceRepository,
        academic_year_repository: AcademicYearRepository,
        teacher_repository: TeacherRepository,
        student_repository: StudentRepository,
    ) -> None:
        self.academic_repository = academic_repository
        self.reference_repository = reference_repository
        self.academic_year_repository = academic_year_repository
        self.teacher_repository = teacher_repository
        self.student_repository = student_repository

    def _require_year(self, academic_year_id: str):
        academic_year = self.academic_year_repository.get_by_id(academic_year_id)
        if not academic_year:
            raise NotFoundException("Academic year not found")
        return academic_year

    def _validate_class_section(self, *, class_id: str, section_id: str | None) -> None:
        class_room = self.reference_repository.get_class(class_id)
        if not class_room:
            raise NotFoundException("Class not found")
        if section_id and not self.reference_repository.get_section_for_class(section_id, class_id):
            raise ValidationException("Section does not belong to the supplied class")

    def _require_teacher(self, teacher_id: str):
        teacher = self.teacher_repository.get_by_id(teacher_id)
        if not teacher:
            raise NotFoundException("Teacher not found")
        return teacher

    def _require_subject(self, subject_id: str):
        subject = self.academic_repository.get_subject(subject_id)
        if not subject:
            raise NotFoundException("Subject not found")
        return subject

    def create_subject(self, payload, *, actor_id: str) -> Subject:
        if self.academic_repository.get_subject_by_name(payload.name):
            raise ConflictException("Subject name already exists")
        if self.academic_repository.get_subject_by_code(payload.code):
            raise ConflictException("Subject code already exists")
        subject = Subject(name=payload.name.strip(), code=payload.code.strip().upper(), is_active=True)
        created = self.academic_repository.create_subject(subject)
        log_audit_event(
            self.academic_repository.db,
            entity_name="SUBJECT",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.academic_repository.db.commit()
        return created

    def update_subject(self, subject_id: str, payload, *, actor_id: str) -> Subject:
        subject = self._require_subject(subject_id)
        old_value = model_to_dict(subject)
        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != subject.name:
            if self.academic_repository.get_subject_by_name(update_data["name"]):
                raise ConflictException("Subject name already exists")
            subject.name = update_data["name"].strip()
        if "code" in update_data and update_data["code"] != subject.code:
            if self.academic_repository.get_subject_by_code(update_data["code"]):
                raise ConflictException("Subject code already exists")
            subject.code = update_data["code"].strip().upper()
        if "is_active" in update_data:
            subject.is_active = update_data["is_active"]

        saved = self.academic_repository.save_subject(subject)
        log_audit_event(
            self.academic_repository.db,
            entity_name="SUBJECT",
            entity_id=saved.id,
            action="UPDATE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.academic_repository.db.commit()
        return saved

    def list_subjects(self) -> list[Subject]:
        return self.academic_repository.list_subjects()

    def create_teacher_subject_assignment(self, payload, *, actor_id: str) -> TeacherSubjectAssignment:
        academic_year = self._require_year(payload.academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        self._validate_class_section(class_id=payload.class_id, section_id=payload.section_id)
        teacher = self._require_teacher(payload.teacher_id)
        subject = self._require_subject(payload.subject_id)
        conflict = self.academic_repository.get_teacher_subject_conflict(
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            subject_id=payload.subject_id,
        )
        if conflict:
            raise ConflictException("A teacher is already mapped to this subject for the selected class scope")

        item = TeacherSubjectAssignment(
            teacher_id=teacher.id,
            subject_id=subject.id,
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
        )
        created = self.academic_repository.create_teacher_subject_assignment(item)
        log_audit_event(
            self.academic_repository.db,
            entity_name="TEACHER_SUBJECT_ASSIGNMENT",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.academic_repository.db.commit()
        return created

    def list_teacher_subject_assignments(
        self,
        *,
        academic_year_id: str | None = None,
        class_id: str | None = None,
        teacher_id: str | None = None,
    ) -> list[TeacherSubjectAssignment]:
        return self.academic_repository.list_teacher_subject_assignments(
            academic_year_id=academic_year_id,
            class_id=class_id,
            teacher_id=teacher_id,
        )

    def _teacher_can_access_subject_scope(
        self,
        *,
        teacher_id: str,
        academic_year_id: str,
        class_id: str,
        section_id: str | None,
        subject_id: str,
    ) -> bool:
        return self.teacher_repository.is_teacher_assigned_to_class(
            teacher_id=teacher_id,
            class_id=class_id,
            section_id=section_id,
            academic_year_id=academic_year_id,
        ) and self.academic_repository.teacher_has_subject_scope(
            teacher_id=teacher_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
        )

    def get_accessible_exam_subject_ids(self, *, teacher_id: str, exam: Exam) -> set[str]:
        accessible_subject_ids: set[str] = set()
        for exam_subject in exam.subjects:
            if self._teacher_can_access_subject_scope(
                teacher_id=teacher_id,
                academic_year_id=exam.academic_year_id,
                class_id=exam.class_id,
                section_id=exam.section_id,
                subject_id=exam_subject.subject_id,
            ):
                accessible_subject_ids.add(str(exam_subject.id))
        return accessible_subject_ids

    def ensure_teacher_can_access_exam_subject(self, *, teacher_id: str, exam_subject_id: str) -> ExamSubject:
        exam_subject = self.academic_repository.get_exam_subject(exam_subject_id)
        if not exam_subject:
            raise NotFoundException("Exam subject not found")
        if not self._teacher_can_access_subject_scope(
            teacher_id=teacher_id,
            academic_year_id=exam_subject.exam.academic_year_id,
            class_id=exam_subject.exam.class_id,
            section_id=exam_subject.exam.section_id,
            subject_id=exam_subject.subject_id,
        ):
            raise AuthorizationException("You do not have access to this marks register")
        return exam_subject

    def create_timetable_entry(self, payload, *, actor_id: str) -> TimetableEntry:
        academic_year = self._require_year(payload.academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        self._validate_class_section(class_id=payload.class_id, section_id=payload.section_id)
        self._require_teacher(payload.teacher_id)
        self._require_subject(payload.subject_id)
        if payload.end_time <= payload.start_time:
            raise ValidationException("End time must be after start time")
        conflict = self.academic_repository.get_timetable_conflict(
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            weekday=payload.weekday.upper(),
            period_label=payload.period_label.strip(),
        )
        if conflict:
            raise ConflictException("A timetable entry already exists for this class, period, and weekday")

        item = TimetableEntry(
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            subject_id=payload.subject_id,
            teacher_id=payload.teacher_id,
            weekday=payload.weekday.upper(),
            period_label=payload.period_label.strip(),
            start_time=payload.start_time,
            end_time=payload.end_time,
            room_label=payload.room_label.strip() if payload.room_label else None,
        )
        created = self.academic_repository.create_timetable_entry(item)
        log_audit_event(
            self.academic_repository.db,
            entity_name="TIMETABLE_ENTRY",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.academic_repository.db.commit()
        return created

    def list_timetable_entries(
        self,
        *,
        academic_year_id: str | None = None,
        class_id: str | None = None,
        section_id: str | None = None,
    ) -> list[TimetableEntry]:
        return self.academic_repository.list_timetable_entries(
            academic_year_id=academic_year_id,
            class_id=class_id,
            section_id=section_id,
        )

    def create_grade_rule(self, payload, *, actor_id: str) -> GradeRule:
        academic_year = self._require_year(payload.academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        if payload.min_percentage < 0 or payload.max_percentage > 100 or payload.min_percentage > payload.max_percentage:
            raise ValidationException("Invalid percentage range supplied")
        if self.academic_repository.get_grade_rule_conflict(
            academic_year_id=payload.academic_year_id,
            grade_label=payload.grade_label,
        ):
            raise ConflictException("Grade label already exists for the academic year")
        for existing in self.academic_repository.list_grade_rules(academic_year_id=payload.academic_year_id):
            if not (payload.max_percentage < existing.min_percentage or payload.min_percentage > existing.max_percentage):
                raise ConflictException("Grade percentage range overlaps with an existing rule")

        item = GradeRule(
            academic_year_id=payload.academic_year_id,
            grade_label=payload.grade_label.strip().upper(),
            min_percentage=payload.min_percentage,
            max_percentage=payload.max_percentage,
            remark=payload.remark.strip() if payload.remark else None,
            sort_order=payload.sort_order,
        )
        created = self.academic_repository.create_grade_rule(item)
        log_audit_event(
            self.academic_repository.db,
            entity_name="GRADE_RULE",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.academic_repository.db.commit()
        return created

    def list_grade_rules(self, *, academic_year_id: str | None = None) -> list[GradeRule]:
        return self.academic_repository.list_grade_rules(academic_year_id=academic_year_id)

    def _build_exam_subjects(self, subject_payloads: list) -> list[ExamSubject]:
        if not subject_payloads:
            raise ValidationException("At least one subject must be included in an exam")
        seen_subjects: set[str] = set()
        subjects: list[ExamSubject] = []
        for item in subject_payloads:
            self._require_subject(item.subject_id)
            if item.subject_id in seen_subjects:
                raise ValidationException("Duplicate subject supplied in exam setup")
            if item.max_marks <= 0 or item.pass_marks < 0 or item.pass_marks > item.max_marks:
                raise ValidationException("Invalid marks threshold supplied")
            seen_subjects.add(str(item.subject_id))
            subjects.append(
                ExamSubject(
                    subject_id=item.subject_id,
                    max_marks=item.max_marks,
                    pass_marks=item.pass_marks,
                )
            )
        return subjects

    def create_exam(self, payload, *, actor_id: str) -> Exam:
        academic_year = self._require_year(payload.academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        self._validate_class_section(class_id=payload.class_id, section_id=payload.section_id)
        if payload.end_date < payload.start_date:
            raise ValidationException("Exam end date cannot be before the start date")

        exam = Exam(
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            section_id=payload.section_id,
            name=payload.name.strip(),
            term_label=payload.term_label.strip() if payload.term_label else None,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=ExamStatus.DRAFT.value,
        )
        exam.subjects = self._build_exam_subjects(payload.subjects)
        created = self.academic_repository.create_exam(exam)
        log_audit_event(
            self.academic_repository.db,
            entity_name="EXAM",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value={
                **model_to_dict(created),
                "subjects": [model_to_dict(item) for item in created.subjects],
            },
        )
        self.academic_repository.db.commit()
        return created

    def update_exam_status(self, exam_id: str, *, status: ExamStatus, actor_id: str) -> Exam:
        exam = self.academic_repository.get_exam(exam_id)
        if not exam:
            raise NotFoundException("Exam not found")
        old_value = model_to_dict(exam)
        exam.status = status.value
        saved = self.academic_repository.save_exam(exam)
        log_audit_event(
            self.academic_repository.db,
            entity_name="EXAM",
            entity_id=saved.id,
            action=f"STATUS_{status.value}",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.academic_repository.db.commit()
        return saved

    def list_exams(self, *, academic_year_id: str | None = None, class_id: str | None = None) -> list[Exam]:
        return self.academic_repository.list_exams(academic_year_id=academic_year_id, class_id=class_id)

    def get_marks_register(self, *, exam_subject_id: str, search: str | None = None) -> list[dict]:
        exam_subject = self.academic_repository.get_exam_subject(exam_subject_id)
        if not exam_subject:
            raise NotFoundException("Exam subject not found")
        students = self.academic_repository.list_students_for_exam(exam=exam_subject.exam, search=search)
        marks_by_student = {
            mark.student_id: mark for mark in self.academic_repository.list_marks_for_exam_subject(exam_subject_id=exam_subject_id)
        }
        rows: list[dict] = []
        for student, _record in students:
            mark = marks_by_student.get(student.id)
            rows.append(
                {
                    "student_id": student.id,
                    "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
                    "student_code": student.student_id,
                    "marks_obtained": mark.marks_obtained if mark else None,
                    "is_absent": bool(mark.is_absent) if mark else False,
                    "remark": mark.remark if mark else None,
                }
            )
        return rows

    def save_marks(self, *, exam_subject_id: str, entries: list, actor_id: str) -> dict:
        exam_subject = self.academic_repository.get_exam_subject(exam_subject_id)
        if not exam_subject:
            raise NotFoundException("Exam subject not found")
        if exam_subject.exam.status == ExamStatus.PUBLISHED.value:
            raise ValidationException("Marks cannot be modified after exam results are published")

        valid_students = {
            str(student.id)
            for student, _record in self.academic_repository.list_students_for_exam(exam=exam_subject.exam)
        }
        processed = 0
        for item in entries:
            student_id = str(item.student_id)
            if student_id not in valid_students:
                raise ValidationException("Student does not belong to the selected exam scope")
            if item.is_absent:
                marks_obtained = None
            else:
                if item.marks_obtained is None:
                    raise ValidationException("Marks are required unless the student is marked absent")
                if item.marks_obtained < 0 or item.marks_obtained > exam_subject.max_marks:
                    raise ValidationException("Marks obtained must be within the subject maximum")
                marks_obtained = item.marks_obtained

            existing = self.academic_repository.get_student_mark(exam_subject_id=exam_subject_id, student_id=student_id)
            if existing:
                existing.marks_obtained = marks_obtained
                existing.is_absent = item.is_absent
                existing.remark = item.remark.strip() if item.remark else None
                self.academic_repository.save_student_mark(existing)
            else:
                self.academic_repository.create_student_mark(
                    StudentMark(
                        exam_subject_id=exam_subject_id,
                        student_id=student_id,
                        marks_obtained=marks_obtained,
                        is_absent=item.is_absent,
                        remark=item.remark.strip() if item.remark else None,
                    )
                )
            processed += 1

        log_audit_event(
            self.academic_repository.db,
            entity_name="STUDENT_MARK",
            entity_id=exam_subject_id,
            action="UPSERT_BATCH",
            performed_by=actor_id,
            new_value={"exam_subject_id": exam_subject_id, "processed_count": processed},
        )
        self.academic_repository.db.commit()
        return {"processed_count": processed}

    def _resolve_grade(self, *, academic_year_id: str, percentage: Decimal) -> tuple[str | None, str | None]:
        for rule in self.academic_repository.list_grade_rules(academic_year_id=academic_year_id):
            if rule.min_percentage <= percentage <= rule.max_percentage:
                return rule.grade_label, rule.remark
        return None, None

    def build_report_card(self, *, exam_id: str, student_id: str) -> dict:
        exam = self.academic_repository.get_exam(exam_id)
        if not exam:
            raise NotFoundException("Exam not found")
        student = self.student_repository.get_by_id(student_id)
        if not student or student.is_deleted:
            raise NotFoundException("Student not found")
        if exam.status != ExamStatus.PUBLISHED.value:
            raise ValidationException("Report cards are available only after exam publication")

        marks = self.academic_repository.list_student_marks_for_exam(exam_id=exam_id, student_id=student_id)
        marks_by_subject = {mark.exam_subject_id: mark for mark in marks}
        total_marks = Decimal("0")
        obtained_marks = Decimal("0")
        subject_rows: list[dict] = []
        overall_result = "PASS"

        for exam_subject in exam.subjects:
            total_marks += Decimal(str(exam_subject.max_marks))
            mark = marks_by_subject.get(exam_subject.id)
            if not mark or mark.is_absent or mark.marks_obtained is None:
                overall_result = "HOLD"
                obtained_value = None
                result = "ABSENT" if mark and mark.is_absent else "PENDING"
            else:
                obtained_value = Decimal(str(mark.marks_obtained))
                obtained_marks += obtained_value
                if obtained_value < Decimal(str(exam_subject.pass_marks)):
                    overall_result = "HOLD"
                    result = "FAIL"
                else:
                    result = "PASS"

            subject_rows.append(
                {
                    "subject_name": exam_subject.subject.name,
                    "max_marks": exam_subject.max_marks,
                    "pass_marks": exam_subject.pass_marks,
                    "marks_obtained": obtained_value,
                    "is_absent": bool(mark.is_absent) if mark else False,
                    "result": result,
                }
            )

        percentage = (obtained_marks / total_marks * Decimal("100")).quantize(Decimal("0.01")) if total_marks else Decimal("0.00")
        overall_grade, overall_remark = self._resolve_grade(
            academic_year_id=exam.academic_year_id,
            percentage=percentage,
        )
        return {
            "exam_id": exam.id,
            "exam_name": exam.name,
            "term_label": exam.term_label,
            "academic_year_name": exam.academic_year.name,
            "class_name": exam.class_room.name,
            "section_name": exam.section.name if exam.section else None,
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
            "student_code": student.student_id,
            "generated_at": utcnow(),
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": percentage,
            "overall_grade": overall_grade,
            "overall_remark": overall_remark,
            "result": overall_result,
            "subject_rows": subject_rows,
        }

    def list_exam_results(self, *, exam_id: str) -> list[dict]:
        exam = self.academic_repository.get_exam(exam_id)
        if not exam:
            raise NotFoundException("Exam not found")
        results: list[dict] = []
        for student, _record in self.academic_repository.list_students_for_exam(exam=exam):
            card = self.build_report_card(exam_id=exam_id, student_id=student.id) if exam.status == ExamStatus.PUBLISHED.value else {
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
                "student_code": student.student_id,
                "result": "DRAFT",
                "percentage": Decimal("0.00"),
                "overall_grade": None,
            }
            results.append(
                {
                    "student_id": card["student_id"],
                    "student_name": card["student_name"],
                    "student_code": card["student_code"],
                    "percentage": card["percentage"],
                    "overall_grade": card["overall_grade"],
                    "result": card["result"],
                }
            )
        return results
