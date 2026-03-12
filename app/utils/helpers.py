"""General helper utilities."""

from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.inspection import inspect


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def success_response(data: Any = None, message: str = "Operation successful") -> dict[str, Any]:
    """Standard API success envelope."""

    return {"success": True, "message": message, "data": data}


def error_response(message: str, error_code: str, details: dict | None = None) -> dict[str, Any]:
    """Standard API error envelope."""

    return {"success": False, "error_code": error_code, "message": message, "details": details or {}}


def generate_receipt_number(prefix: str) -> str:
    """Generate a human-readable receipt number."""

    return f"{prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"


def model_to_dict(instance: Any, *, exclude: Iterable[str] | None = None) -> dict[str, Any]:
    """Serialize a SQLAlchemy model into a plain dictionary for audit storage."""

    exclude_set = set(exclude or [])
    values: dict[str, Any] = {}
    for column in inspect(instance).mapper.column_attrs:
        key = column.key
        if key in exclude_set:
            continue
        value = getattr(instance, key)
        if hasattr(value, "value"):
            value = value.value
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        if isinstance(value, UUID):
            value = str(value)
        if isinstance(value, Decimal):
            value = str(value)
        values[key] = value
    return values
