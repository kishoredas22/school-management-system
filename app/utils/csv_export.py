"""CSV export helpers."""

import csv
from io import StringIO

from fastapi import Response


def build_csv_response(*, filename: str, headers: list[str], rows: list[list[object]]) -> Response:
    """Return a CSV response with a download-friendly filename."""

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
