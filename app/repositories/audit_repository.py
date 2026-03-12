"""Audit log data access layer."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.models.audit_log import AuditLog
from app.models.enums import AuditReviewStatus
from app.models.user import User


class AuditRepository:
    """Repository for audit log queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self):
        return select(AuditLog).options(
            joinedload(AuditLog.actor),
            joinedload(AuditLog.reviewer),
        )

    def _build_filtered_query(
        self,
        *,
        entity_name: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        review_status: AuditReviewStatus | None = None,
        requires_review: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        query = self._base_query()
        actor_alias = aliased(User)

        if entity_name:
            query = query.where(AuditLog.entity_name.ilike(f"%{entity_name.strip()}%"))
        if action:
            query = query.where(AuditLog.action.ilike(f"%{action.strip()}%"))
        if actor:
            term = f"%{actor.strip()}%"
            query = (
                query.outerjoin(actor_alias, AuditLog.performed_by == actor_alias.id)
                .where(
                    or_(
                        actor_alias.username.ilike(term),
                        AuditLog.performed_by.cast(String).ilike(term),
                    )
                )
            )
        if review_status:
            query = query.where(AuditLog.review_status == review_status)
        if requires_review is not None:
            query = query.where(AuditLog.requires_review.is_(requires_review))
        if date_from:
            start_at = datetime.combine(date_from, time.min)
            query = query.where(AuditLog.performed_at >= start_at)
        if date_to:
            end_before = datetime.combine(date_to + timedelta(days=1), time.min)
            query = query.where(AuditLog.performed_at < end_before)
        return query.order_by(AuditLog.performed_at.desc())

    def list_logs(
        self,
        *,
        page: int,
        size: int,
        entity_name: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        review_status: AuditReviewStatus | None = None,
        requires_review: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[AuditLog], int]:
        query = self._build_filtered_query(
            entity_name=entity_name,
            action=action,
            actor=actor,
            review_status=review_status,
            requires_review=requires_review,
            date_from=date_from,
            date_to=date_to,
        )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.execute(query.offset((page - 1) * size).limit(size)).unique().scalars().all()
        return items, total

    def export_logs(
        self,
        *,
        entity_name: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        review_status: AuditReviewStatus | None = None,
        requires_review: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[AuditLog]:
        query = self._build_filtered_query(
            entity_name=entity_name,
            action=action,
            actor=actor,
            review_status=review_status,
            requires_review=requires_review,
            date_from=date_from,
            date_to=date_to,
        )
        return self.db.execute(query).unique().scalars().all()

    def get_summary(self) -> dict[str, int]:
        total = self.db.scalar(select(func.count()).select_from(AuditLog)) or 0
        review_required = self.db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.requires_review.is_(True))
        ) or 0
        pending = self.db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.review_status == AuditReviewStatus.PENDING)
        ) or 0
        approved = self.db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.review_status == AuditReviewStatus.APPROVED)
        ) or 0
        rejected = self.db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.review_status == AuditReviewStatus.REJECTED)
        ) or 0
        return {
            "total_logs": int(total),
            "review_required": int(review_required),
            "pending_reviews": int(pending),
            "approved_reviews": int(approved),
            "rejected_reviews": int(rejected),
        }

    def get_by_id(self, audit_log_id: str) -> AuditLog | None:
        return (
            self.db.execute(self._base_query().where(AuditLog.id == audit_log_id))
            .unique()
            .scalar_one_or_none()
        )

    def save(self, item: AuditLog) -> AuditLog:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item
