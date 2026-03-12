# Deployment Summary

## Runtime Model

- Containerized FastAPI service
- PostgreSQL database
- Alembic migrations on startup
- Seed script for baseline roles and reference data

## Cloud Targets From Source Docs

- Cloud Run
- Cloud SQL
- Secret Manager
- HTTPS via managed certificates

## Local Deployment

Use `docker compose up --build`.

## Reverse Proxy Layout

- `frontend` serves the built React app on container port `5173`
- `frontend` also proxies `/api/` to the FastAPI service so direct local access on `http://localhost:5173` still works
- `nginx` exposes a shared entrypoint on `http://localhost:8080`
- `nginx` forwards `/` to `frontend` and `/api/` to `api`

## Ngrok Access

Use the optional `ngrok` Compose profile when you want to expose the app outside your local network.

Required env:

```env
NGROK_AUTHTOKEN=your-token-here
```

Optional reserved domain:

```env
NGROK_DOMAIN=your-reserved-domain.ngrok-free.app
```

Run:

```bash
docker compose --profile ngrok up --build
```

Then:

- open `http://localhost:4040` to inspect the tunnel
- share the HTTPS public URL from `ngrok`
- keep using `http://localhost:8080` locally if you want to test the same proxied entrypoint without leaving your machine
