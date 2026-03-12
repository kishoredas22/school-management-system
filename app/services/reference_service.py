"""Reference-data business logic."""

from app.core.exceptions import ConflictException, NotFoundException
from app.models.reference import ClassRoom, Section
from app.repositories.reference_repository import ReferenceRepository
from app.utils.audit_logger import log_audit_event
from app.utils.helpers import model_to_dict


class ReferenceService:
    """Business logic for class and section management."""

    def __init__(self, repository: ReferenceRepository) -> None:
        self.repository = repository

    def create_class(self, *, name: str, actor_id: str) -> ClassRoom:
        if self.repository.get_class_by_name(name):
            raise ConflictException("Class name already exists")

        created = self.repository.create_class(ClassRoom(name=name.strip()))
        log_audit_event(
            self.repository.db,
            entity_name="CLASS",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.repository.db.commit()
        return created

    def create_section(self, *, name: str, class_id: str, actor_id: str) -> Section:
        class_room = self.repository.get_class(class_id)
        if not class_room:
            raise NotFoundException("Class not found")
        if self.repository.get_section_by_name(class_id=class_id, name=name):
            raise ConflictException("Section name already exists for the supplied class")

        created = self.repository.create_section(Section(name=name.strip(), class_id=class_id))
        log_audit_event(
            self.repository.db,
            entity_name="SECTION",
            entity_id=created.id,
            action="CREATE",
            performed_by=actor_id,
            new_value=model_to_dict(created),
        )
        self.repository.db.commit()
        return created
