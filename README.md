# School Management System

Production-oriented school management system generated from the uploaded BRD/FRD/API/DB/architecture documents. The repository now contains the FastAPI backend and a responsive React frontend.

## Scope Implemented

- JWT authentication with role-based access control
- User management for `SUPER_ADMIN`
- Academic year lifecycle with close/lock behavior
- Student creation, listing, updating, status changes, and promotion workflow
- Student and teacher attendance management
- Fee structures, immutable fee payments, fee summaries, and printable fee receipts
- Teacher profiles, assignments, contracts, salary payments, and printable salary slips
- Fee, attendance, teacher-payment, and audit reports
- Structured logging, Docker support, Alembic migrations, and seed data

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- ReportLab
- React 18
- TypeScript
- Vite

## Run With Docker

```bash
docker compose up --build
```

Unified app URL: `http://localhost:8080`
Frontend debug URL: `http://localhost:5173`
API base URL: `http://localhost:8000/api/v1`

Seeded super admin:

- Username: `superadmin`
- Password: `password123`

## Run Locally

1. Create a virtual environment and install backend dependencies:

```bash
pip install -r requirements.txt
```

2. Update `.env` if needed.

3. Run migrations and seed data:

```bash
alembic upgrade head
python scripts/seed_data.py
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

5. Start the frontend in a second terminal:

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend local URL: `http://localhost:5173`

## Frontend Notes

- The frontend is in `frontend/`
- Local frontend development requires Node.js 20+ and npm
- Local frontend development uses `frontend/.env` and defaults to `http://localhost:8000/api/v1`
- Docker builds point the frontend at `/api/v1` and rely on container-side proxying, so the same image works behind the shared reverse proxy and `ngrok`
- Email-link sign-in URLs use `FRONTEND_APP_URL`, so set that env var to your real app URL before sharing email login links outside localhost
- The UI is role-aware and exposes screens for dashboard, students, teachers, fees, attendance, reports, audit logs, and user access management
- The visual design uses a custom editorial-style interface instead of a stock admin template

## Access From Another Network With Ngrok

1. Put your `ngrok` auth token in [`.env`](./.env):

```env
NGROK_AUTHTOKEN=your-token-here
```

2. If you have a reserved domain, also set:

```env
NGROK_DOMAIN=your-reserved-domain.ngrok-free.app
```

3. Start the stack with the `ngrok` profile:

```bash
docker compose --profile ngrok up --build
```

4. Open the app locally at `http://localhost:8080`.

5. Check the tunnel inspector at `http://localhost:4040` and use the public HTTPS URL shown there.

The tunnel points to the shared Nginx entrypoint, so remote users load the frontend and `/api/v1` from the same public origin without extra frontend reconfiguration.

## Tests

```bash
pytest
```

## Important Notes

- The source documents explicitly require teacher assignment restrictions and teacher-role attendance access, but they do not define how a login user links to a teacher profile. This implementation adds an internal optional `users.teacher_id` link to satisfy that requirement.
- The source documents require teacher assigned classes but do not define a persistence structure. This implementation adds an internal `teacher_class_assignments` table.
- The promotion workflow documents do not define class progression order or target-class mapping. To avoid inventing undocumented rules, promotion into a new academic year preserves the existing class and section. This is documented in [`docs/IMPLEMENTATION_NOTES.md`](./docs/IMPLEMENTATION_NOTES.md).
