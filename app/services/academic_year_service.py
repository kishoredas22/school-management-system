"""Academic year business logic."""

from datetime import date

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.academic_year import AcademicYear
from app.repositories.academic_year_repository import AcademicYearRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict


class AcademicYearService:
    """Business logic for academic year lifecycle management."""

    def __init__(self, repository: AcademicYearRepository) -> None:
        self.repository = repository

    def create_academic_year(self, *, name: str, start_date: date, end_date: date, actor_id: str) -> AcademicYear:
        if start_date >= end_date:
            raise ValidationException("Academic year start_date must be before end_date")
        if self.repository.get_by_name(name):
            raise ConflictException("Academic year name already exists")

        is_active = self.repository.get_active() is None
        academic_year = AcademicYear(
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            is_closed=False,
        )
        created = self.repository.create(academic_year)
        log_audit_event(
            self.repository.db,
            entity_name="ACADEMIC_YEAR",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.repository.db.commit()
        return created

    def list_academic_years(self) -> list[AcademicYear]:
        return self.repository.list_all()

    def get_active_year(self) -> AcademicYear:
        year = self.repository.get_active()
        if not year:
            raise NotFoundException("No active academic year found")
        return year

    def get_by_id(self, academic_year_id: str) -> AcademicYear:
        academic_year = self.repository.get_by_id(academic_year_id)
        if not academic_year:
            raise NotFoundException("Academic year not found")
        return academic_year

    def ensure_year_is_open(self, academic_year_id: str) -> AcademicYear:
        academic_year = self.get_by_id(academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year modification is not allowed")
        return academic_year

    def close_academic_year(self, *, academic_year_id: str, actor_id: str) -> AcademicYear:
        academic_year = self.get_by_id(academic_year_id)
        if academic_year.is_closed:
            return academic_year

        old_value = model_to_dict(academic_year)
        academic_year.is_closed = True
        academic_year.is_active = False
        saved = self.repository.save(academic_year)
        log_audit_event(
            self.repository.db,
            entity_name="ACADEMIC_YEAR",
            entity_id=saved.id,
            action="CLOSE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.repository.db.commit()
        return saved

    def activate_academic_year(self, *, academic_year_id: str, actor_id: str) -> AcademicYear:
        academic_year = self.get_by_id(academic_year_id)
        if academic_year.is_closed:
            raise ValidationException("Closed academic year cannot be activated")
        if academic_year.is_active:
            return academic_year

        self.repository.deactivate_all()
        old_value = model_to_dict(academic_year)
        academic_year.is_active = True
        saved = self.repository.save(academic_year)
        log_audit_event(
            self.repository.db,
            entity_name="ACADEMIC_YEAR",
            entity_id=saved.id,
            action="ACTIVATE",
            performed_by=actor_id,
            old_value=old_value,
            new_value=model_to_dict(saved),
        )
        self.repository.db.commit()
        return saved
