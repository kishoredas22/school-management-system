"""Reference data access layer."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reference import ClassRoom, Section


class ReferenceRepository:
    """Repository for classes and sections."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_class(self, class_id: str) -> ClassRoom | None:
        return self.db.scalar(select(ClassRoom).where(ClassRoom.id == class_id))

    def get_class_by_name(self, name: str) -> ClassRoom | None:
        return self.db.scalar(select(ClassRoom).where(ClassRoom.name == name.strip()))

    def get_section(self, section_id: str) -> Section | None:
        return self.db.scalar(select(Section).where(Section.id == section_id))

    def get_section_by_name(self, *, class_id: str, name: str) -> Section | None:
        return self.db.scalar(select(Section).where(Section.class_id == class_id, Section.name == name.strip()))

    def get_section_for_class(self, section_id: str, class_id: str) -> Section | None:
        return self.db.scalar(select(Section).where(Section.id == section_id, Section.class_id == class_id))

    def list_classes(self) -> list[ClassRoom]:
        return self.db.scalars(select(ClassRoom).order_by(ClassRoom.name)).all()

    def list_sections(self, class_id: str | None = None) -> list[Section]:
        query = select(Section).order_by(Section.name)
        if class_id:
            query = query.where(Section.class_id == class_id)
        return self.db.scalars(query).all()

    def create_class(self, class_room: ClassRoom) -> ClassRoom:
        self.db.add(class_room)
        self.db.flush()
        self.db.refresh(class_room)
        return class_room

    def create_section(self, section: Section) -> Section:
        self.db.add(section)
        self.db.flush()
        self.db.refresh(section)
        return section
