"""Audit business logic."""

from datetime import date

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.enums import AuditReviewStatus
from app.repositories.audit_repository import AuditRepository
from app.utils.helpers import utcnow
from app.utils.pagination import build_pagination


class AuditService:
    """Business logic for audit log access and governance review."""

    def __init__(self, repository: AuditRepository) -> None:
        self.repository = repository

    def _resolve_review_status(self, review_status: str | None) -> AuditReviewStatus | None:
        if not review_status:
            return None
        try:
            return AuditReviewStatus(review_status)
        except ValueError as exc:
            raise ValidationException("Invalid review status supplied") from exc

    def list_logs(
        self,
        *,
        page: int,
        size: int,
        entity_name: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        review_status: str | None = None,
        requires_review: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        resolved_status = self._resolve_review_status(review_status)
        items, total = self.repository.list_logs(
            page=page,
            size=size,
            entity_name=entity_name,
            action=action,
            actor=actor,
            review_status=resolved_status,
            requires_review=requires_review,
            date_from=date_from,
            date_to=date_to,
        )
        return build_pagination(page, size, total, items)

    def export_logs(
        self,
        *,
        entity_name: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        review_status: str | None = None,
        requires_review: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        resolved_status = self._resolve_review_status(review_status)
        return self.repository.export_logs(
            entity_name=entity_name,
            action=action,
            actor=actor,
            review_status=resolved_status,
            requires_review=requires_review,
            date_from=date_from,
            date_to=date_to,
        )

    def summary(self) -> dict[str, int]:
        return self.repository.get_summary()

    def review_log(
        self,
        *,
        audit_log_id: str,
        status: str,
        review_note: str | None,
        reviewer_id: str,
    ):
        try:
            resolved_status = AuditReviewStatus(status)
        except ValueError as exc:
            raise ValidationException("Invalid review status supplied") from exc

        if resolved_status not in {AuditReviewStatus.APPROVED, AuditReviewStatus.REJECTED}:
            raise ValidationException("Review status must be APPROVED or REJECTED")

        item = self.repository.get_by_id(audit_log_id)
        if not item:
            raise NotFoundException("Audit log not found")
        if not item.requires_review:
            raise ValidationException("This audit event does not require governance review")
        if item.review_status != AuditReviewStatus.PENDING:
            raise ConflictException("This audit event has already been reviewed")

        item.review_status = resolved_status
        item.review_note = (review_note or "").strip() or None
        item.reviewed_by = reviewer_id
        item.reviewed_at = utcnow()
        saved = self.repository.save(item)
        self.repository.db.commit()
        return saved
