"""Audit logging helper."""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditReviewStatus


SENSITIVE_REVIEW_ACTIONS: set[tuple[str, str]] = {
    ("ACADEMIC_YEAR", "ACTIVATE"),
    ("ACADEMIC_YEAR", "CLOSE"),
    ("FEE_PAYMENT", "CREATE"),
    ("STUDENT", "STATUS_CHANGE"),
    ("TEACHER_PAYMENT", "CREATE"),
    ("USER", "CREATE"),
    ("USER", "UPDATE"),
}


def _resolve_review_state(
    *,
    entity_name: str,
    action: str,
    requires_review: bool | None,
) -> tuple[bool, AuditReviewStatus]:
    should_review = requires_review
    if should_review is None:
        should_review = (entity_name, action) in SENSITIVE_REVIEW_ACTIONS
    return should_review, AuditReviewStatus.PENDING if should_review else AuditReviewStatus.NOT_REQUIRED


def log_audit_event(
    db: Session,
    *,
    entity_name: str,
    entity_id: str | None,
    action: str,
    performed_by: str | None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    requires_review: bool | None = None,
) -> AuditLog:
    """Persist an immutable audit record."""

    should_review, review_status = _resolve_review_state(
        entity_name=entity_name,
        action=action,
        requires_review=requires_review,
    )
    entry = AuditLog(
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by,
        requires_review=should_review,
        review_status=review_status,
    )
    db.add(entry)
    db.flush()
    return entry
