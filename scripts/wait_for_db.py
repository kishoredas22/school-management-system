"""Wait for the configured database to accept connections."""

from __future__ import annotations

import sys
import time

import psycopg
from sqlalchemy.engine import make_url

from app.core.config import settings


def _build_psycopg_conninfo() -> str:
    url = make_url(settings.database_url)
    return (
        f"host={url.host or 'localhost'} "
        f"port={url.port or 5432} "
        f"dbname={url.database or ''} "
        f"user={url.username or ''} "
        f"password={url.password or ''}"
    ).strip()


def main() -> int:
    attempts = 30
    delay_seconds = 2
    conninfo = _build_psycopg_conninfo()

    for attempt in range(1, attempts + 1):
        try:
            with psycopg.connect(conninfo, connect_timeout=5):
                print("Database is ready.")
                return 0
        except psycopg.OperationalError as exc:
            print(f"Waiting for database ({attempt}/{attempts}): {exc}")
            time.sleep(delay_seconds)

    print("Database did not become ready in time.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
