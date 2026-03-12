"""Academic year data access layer."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear


class AcademicYearRepository:
    """Repository for academic year persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, academic_year: AcademicYear) -> AcademicYear:
        self.db.add(academic_year)
        self.db.flush()
        self.db.refresh(academic_year)
        return academic_year

    def list_all(self) -> list[AcademicYear]:
        return self.db.scalars(select(AcademicYear).order_by(AcademicYear.start_date.desc())).all()

    def get_by_id(self, academic_year_id: str) -> AcademicYear | None:
        return self.db.scalar(select(AcademicYear).where(AcademicYear.id == academic_year_id))

    def get_by_name(self, name: str) -> AcademicYear | None:
        return self.db.scalar(select(AcademicYear).where(AcademicYear.name == name))

    def get_active(self) -> AcademicYear | None:
        return self.db.scalar(select(AcademicYear).where(AcademicYear.is_active.is_(True)))

    def deactivate_all(self) -> None:
        self.db.execute(update(AcademicYear).values(is_active=False))

    def save(self, academic_year: AcademicYear) -> AcademicYear:
        self.db.add(academic_year)
        self.db.flush()
        self.db.refresh(academic_year)
        return academic_year
