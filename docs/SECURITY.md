# Security Summary

- JWT authentication for protected endpoints
- Password hashing with bcrypt
- Role validation at route and service boundaries
- CORS restrictions via environment configuration
- No direct database exposure
- Structured audit logging for key state changes

## Roles

- `SUPER_ADMIN`
- `ADMIN`
- `TEACHER`
- `DATA_ENTRY`
