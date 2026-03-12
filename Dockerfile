FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY frontend/src/assets ./frontend/src/assets
COPY scripts ./scripts
COPY tests ./tests
COPY README.md .

CMD ["sh", "-c", "python scripts/wait_for_db.py && alembic upgrade head && python scripts/seed_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
