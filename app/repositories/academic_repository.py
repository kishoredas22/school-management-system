"""Academic management data access layer."""

from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.academic import Exam, ExamSubject, GradeRule, StudentMark, Subject, TeacherSubjectAssignment, TimetableEntry
from app.models.reference import ClassRoom, Section
from app.models.student import Student, StudentAcademicRecord
from app.models.teacher import Teacher


class AcademicRepository:
    """Repository for academic management entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_subject_by_name(self, name: str) -> Subject | None:
        return self.db.scalar(select(Subject).where(Subject.name == name.strip()))

    def get_subject_by_code(self, code: str) -> Subject | None:
        return self.db.scalar(select(Subject).where(Subject.code == code.strip().upper()))

    def get_subject(self, subject_id: str) -> Subject | None:
        return self.db.scalar(select(Subject).where(Subject.id == subject_id))

    def list_subjects(self) -> list[Subject]:
        return self.db.scalars(select(Subject).order_by(Subject.name)).all()

    def create_subject(self, subject: Subject) -> Subject:
        self.db.add(subject)
        self.db.flush()
        self.db.refresh(subject)
        return subject

    def save_subject(self, subject: Subject) -> Subject:
        self.db.add(subject)
        self.db.flush()
        self.db.refresh(subject)
        return subject

    def get_teacher_subject_conflict(
        self,
        *,
        academic_year_id: str,
        class_id: str,
        section_id: str | None,
        subject_id: str,
    ) -> TeacherSubjectAssignment | None:
        return self.db.scalar(
            select(TeacherSubjectAssignment).where(
                TeacherSubjectAssignment.academic_year_id == academic_year_id,
                TeacherSubjectAssignment.class_id == class_id,
                TeacherSubjectAssignment.section_id == section_id,
                TeacherSubjectAssignment.subject_id == subject_id,
            )
        )

    def create_teacher_subject_assignment(self, item: TeacherSubjectAssignment) -> TeacherSubjectAssignment:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def list_teacher_subject_assignments(
        self,
        *,
        academic_year_id: str | None = None,
        class_id: str | None = None,
        teacher_id: str | None = None,
    ) -> list[TeacherSubjectAssignment]:
        query = (
            select(TeacherSubjectAssignment)
            .options(
                joinedload(TeacherSubjectAssignment.teacher),
                joinedload(TeacherSubjectAssignment.subject),
                joinedload(TeacherSubjectAssignment.class_room),
                joinedload(TeacherSubjectAssignment.section),
                joinedload(TeacherSubjectAssignment.academic_year),
            )
            .order_by(TeacherSubjectAssignment.created_at.desc())
        )
        if academic_year_id:
            query = query.where(TeacherSubjectAssignment.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(TeacherSubjectAssignment.class_id == class_id)
        if teacher_id:
            query = query.where(TeacherSubjectAssignment.teacher_id == teacher_id)
        return self.db.scalars(query).all()

    def get_timetable_conflict(
        self,
        *,
        academic_year_id: str,
        class_id: str,
        section_id: str | None,
        weekday: str,
        period_label: str,
    ) -> TimetableEntry | None:
        return self.db.scalar(
            select(TimetableEntry).where(
                TimetableEntry.academic_year_id == academic_year_id,
                TimetableEntry.class_id == class_id,
                TimetableEntry.section_id == section_id,
                TimetableEntry.weekday == weekday,
                TimetableEntry.period_label == period_label,
            )
        )

    def create_timetable_entry(self, item: TimetableEntry) -> TimetableEntry:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def list_timetable_entries(
        self,
        *,
        academic_year_id: str | None = None,
        class_id: str | None = None,
        section_id: str | None = None,
    ) -> list[TimetableEntry]:
        query = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.teacher),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.class_room),
                joinedload(TimetableEntry.section),
                joinedload(TimetableEntry.academic_year),
            )
            .order_by(TimetableEntry.weekday, TimetableEntry.start_time)
        )
        if academic_year_id:
            query = query.where(TimetableEntry.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(TimetableEntry.class_id == class_id)
        if section_id:
            query = query.where(TimetableEntry.section_id == section_id)
        return self.db.scalars(query).all()

    def get_grade_rule_conflict(self, *, academic_year_id: str, grade_label: str) -> GradeRule | None:
        return self.db.scalar(
            select(GradeRule).where(
                GradeRule.academic_year_id == academic_year_id,
                GradeRule.grade_label == grade_label.strip().upper(),
            )
        )

    def list_grade_rules(self, *, academic_year_id: str | None = None) -> list[GradeRule]:
        query = select(GradeRule).order_by(GradeRule.sort_order, GradeRule.max_percentage.desc())
        if academic_year_id:
            query = query.where(GradeRule.academic_year_id == academic_year_id)
        return self.db.scalars(query).all()

    def create_grade_rule(self, item: GradeRule) -> GradeRule:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def create_exam(self, exam: Exam) -> Exam:
        self.db.add(exam)
        self.db.flush()
        self.db.refresh(exam)
        return exam

    def get_exam(self, exam_id: str) -> Exam | None:
        return self.db.scalar(
            select(Exam)
            .options(
                joinedload(Exam.academic_year),
                joinedload(Exam.class_room),
                joinedload(Exam.section),
                joinedload(Exam.subjects).joinedload(ExamSubject.subject),
            )
            .where(Exam.id == exam_id)
        )

    def list_exams(
        self,
        *,
        academic_year_id: str | None = None,
        class_id: str | None = None,
    ) -> list[Exam]:
        query = (
            select(Exam)
            .options(
                joinedload(Exam.class_room),
                joinedload(Exam.section),
                joinedload(Exam.academic_year),
                joinedload(Exam.subjects).joinedload(ExamSubject.subject),
            )
            .order_by(Exam.start_date.desc(), Exam.name)
        )
        if academic_year_id:
            query = query.where(Exam.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(Exam.class_id == class_id)
        return self.db.execute(query).unique().scalars().all()

    def save_exam(self, exam: Exam) -> Exam:
        self.db.add(exam)
        self.db.flush()
        self.db.refresh(exam)
        return exam

    def replace_exam_subjects(self, exam: Exam, subjects: list[ExamSubject]) -> None:
        exam.subjects.clear()
        exam.subjects.extend(subjects)
        self.db.flush()

    def get_exam_subject(self, exam_subject_id: str) -> ExamSubject | None:
        return self.db.scalar(
            select(ExamSubject)
            .options(
                joinedload(ExamSubject.exam).joinedload(Exam.academic_year),
                joinedload(ExamSubject.exam).joinedload(Exam.class_room),
                joinedload(ExamSubject.exam).joinedload(Exam.section),
                joinedload(ExamSubject.subject),
            )
            .where(ExamSubject.id == exam_subject_id)
        )

    def list_students_for_exam(self, *, exam: Exam, search: str | None = None) -> Sequence[tuple[Student, StudentAcademicRecord]]:
        query: Select = (
            select(Student, StudentAcademicRecord)
            .join(StudentAcademicRecord, StudentAcademicRecord.student_id == Student.id)
            .where(
                Student.is_deleted.is_(False),
                Student.status == "ACTIVE",
                StudentAcademicRecord.academic_year_id == exam.academic_year_id,
                StudentAcademicRecord.class_id == exam.class_id,
            )
        )
        if exam.section_id:
            query = query.where(StudentAcademicRecord.section_id == exam.section_id)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Student.first_name.ilike(term),
                    Student.last_name.ilike(term),
                    Student.student_id.ilike(term),
                )
            )
        return self.db.execute(query.order_by(Student.first_name, Student.last_name)).all()

    def list_marks_for_exam_subject(self, *, exam_subject_id: str) -> list[StudentMark]:
        return self.db.scalars(
            select(StudentMark)
            .options(joinedload(StudentMark.student))
            .where(StudentMark.exam_subject_id == exam_subject_id)
        ).all()

    def create_student_mark(self, mark: StudentMark) -> StudentMark:
        self.db.add(mark)
        self.db.flush()
        self.db.refresh(mark)
        return mark

    def save_student_mark(self, mark: StudentMark) -> StudentMark:
        self.db.add(mark)
        self.db.flush()
        self.db.refresh(mark)
        return mark

    def get_student_mark(self, *, exam_subject_id: str, student_id: str) -> StudentMark | None:
        return self.db.scalar(
            select(StudentMark).where(
                StudentMark.exam_subject_id == exam_subject_id,
                StudentMark.student_id == student_id,
            )
        )

    def list_student_marks_for_exam(self, *, exam_id: str, student_id: str) -> list[StudentMark]:
        query = (
            select(StudentMark)
            .join(ExamSubject, ExamSubject.id == StudentMark.exam_subject_id)
            .options(
                joinedload(StudentMark.exam_subject).joinedload(ExamSubject.subject),
            )
            .where(
                StudentMark.student_id == student_id,
                ExamSubject.exam_id == exam_id,
            )
        )
        return self.db.scalars(query).all()

    def list_exam_results(self, *, exam_id: str) -> list[tuple[Student, StudentAcademicRecord]]:
        exam = self.get_exam(exam_id)
        if not exam:
            return []
        return self.list_students_for_exam(exam=exam)

    def list_teachers(self) -> list[Teacher]:
        return self.db.scalars(select(Teacher).where(Teacher.is_deleted.is_(False)).order_by(Teacher.name)).all()

    def save(self, item):
        self.db.add(item)
        self.db.flush()
        return item
