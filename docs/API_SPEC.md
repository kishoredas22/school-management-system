# API Summary

Base URL: `/api/v1`

## Authentication

- `POST /auth/login`
- `POST /auth/logout`

## Users

- `POST /users`
- `GET /users`

## Academic Years

- `POST /academic-years`
- `GET /academic-years`
- `PUT /academic-years/{id}/close`

## Students

- `POST /students`
- `GET /students`
- `PUT /students/{id}`
- `PUT /students/{id}/status`
- `POST /students/promote`

## Attendance

- `POST /attendance/students`
- `POST /attendance/teachers`

## Fees

- `POST /fees/structures`
- `POST /fees/payments`
- `GET /fees/payments/student/{id}`
- `GET /fees/payments/{payment_id}/receipt`

## Teachers

- `POST /teachers`
- `GET /teachers`
- `PUT /teachers/{id}`
- `POST /teachers/contracts`
- `POST /teachers/payments`
- `GET /teachers/payments/{payment_id}/slip`

## Reports

- `GET /reports/fees`
- `GET /reports/fees/pending`
- `GET /reports/attendance/students`
- `GET /reports/attendance/details`
- `GET /reports/teacher-payments`
- `GET /reports/teacher-payments/details`

## Audit

- `GET /audit-logs`
