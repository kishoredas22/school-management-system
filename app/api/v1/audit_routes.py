"""Audit endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.dependencies import require_permissions, require_roles
from app.models.enums import PermissionCode, RoleName
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_schema import AuditReviewRequest
from app.services.audit_service import AuditService
from app.utils.csv_export import build_csv_response
from app.utils.helpers import success_response

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _serialize_audit_log(item):
    return {
        "id": item.id,
        "entity_name": item.entity_name,
        "entity_id": item.entity_id,
        "action": item.action,
        "performed_by": item.performed_by,
        "performed_by_username": item.actor.username if item.actor else None,
        "old_value": item.old_value,
        "new_value": item.new_value,
        "performed_at": item.performed_at,
        "requires_review": item.requires_review,
        "review_status": item.review_status.value,
        "review_note": item.review_note,
        "reviewed_by": item.reviewed_by,
        "reviewed_by_username": item.reviewer.username if item.reviewer else None,
        "reviewed_at": item.reviewed_at,
    }


def _audit_service(db):
    return AuditService(AuditRepository(db))


@router.get("/summary")
def get_audit_summary(
    _=Depends(require_roles(RoleName.SUPER_ADMIN)),
    __=Depends(require_permissions(PermissionCode.AUDIT_VIEW)),
    db=Depends(get_db),
):
    data = _audit_service(db).summary()
    return success_response(data=data, message="Audit summary retrieved")


@router.get("/export")
def export_audit_logs(
    entity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    requires_review: bool | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _=Depends(require_roles(RoleName.SUPER_ADMIN)),
    __=Depends(require_permissions(PermissionCode.AUDIT_VIEW)),
    db=Depends(get_db),
):
    items = _audit_service(db).export_logs(
        entity_name=entity,
        action=action,
        actor=actor,
        review_status=review_status,
        requires_review=requires_review,
        date_from=date_from,
        date_to=date_to,
    )
    return build_csv_response(
        filename="audit-log-export.csv",
        headers=[
            "Entity",
            "Entity ID",
            "Action",
            "Actor",
            "Performed At",
            "Requires Review",
            "Review Status",
            "Reviewed By",
            "Reviewed At",
            "Review Note",
        ],
        rows=[
            [
                item.entity_name,
                item.entity_id,
                item.action,
                item.actor.username if item.actor else item.performed_by or "System",
                item.performed_at.isoformat(),
                "Yes" if item.requires_review else "No",
                item.review_status.value,
                item.reviewer.username if item.reviewer else item.reviewed_by,
                item.reviewed_at.isoformat() if item.reviewed_at else "",
                item.review_note or "",
            ]
            for item in items
        ],
    )


@router.post("/{audit_log_id}/review")
def review_audit_log(
    audit_log_id: UUID,
    payload: AuditReviewRequest,
    current_user=Depends(require_roles(RoleName.SUPER_ADMIN)),
    __=Depends(require_permissions(PermissionCode.AUDIT_VIEW)),
    db=Depends(get_db),
):
    service = _audit_service(db)
    item = service.review_log(
        audit_log_id=audit_log_id,
        status=payload.status,
        review_note=payload.review_note,
        reviewer_id=current_user.id,
    )
    return success_response(data=_serialize_audit_log(item), message="Audit event reviewed")


@router.get("")
def list_audit_logs(
    entity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    requires_review: bool | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _=Depends(require_roles(RoleName.SUPER_ADMIN)),
    __=Depends(require_permissions(PermissionCode.AUDIT_VIEW)),
    db=Depends(get_db),
):
    data = _audit_service(db).list_logs(
        page=page,
        size=size,
        entity_name=entity,
        action=action,
        actor=actor,
        review_status=review_status,
        requires_review=requires_review,
        date_from=date_from,
        date_to=date_to,
    )
    payload = data.to_dict()
    payload["data"] = [_serialize_audit_log(item) for item in data.data]
    return success_response(data=payload, message="Audit logs retrieved")
