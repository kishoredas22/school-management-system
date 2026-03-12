"""Pagination helpers."""

from dataclasses import dataclass
from math import ceil
from typing import Any


@dataclass(slots=True)
class PaginationResult:
    """Paginated collection response."""

    page: int
    size: int
    total_records: int
    total_pages: int
    data: list[Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize pagination metadata into a response-safe dictionary."""

        return {
            "page": self.page,
            "size": self.size,
            "total_records": self.total_records,
            "total_pages": self.total_pages,
            "data": self.data,
        }


def build_pagination(page: int, size: int, total_records: int, data: list[Any]) -> PaginationResult:
    """Build pagination metadata."""

    total_pages = ceil(total_records / size) if size else 1
    return PaginationResult(
        page=page,
        size=size,
        total_records=total_records,
        total_pages=total_pages,
        data=data,
    )
