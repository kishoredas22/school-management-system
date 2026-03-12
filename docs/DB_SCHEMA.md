# Database Summary

## Core Tables

- `roles`
- `users`
- `academic_years`
- `classes`
- `sections`
- `students`
- `student_academic_records`
- `teachers`
- `teacher_class_assignments`
- `teacher_contracts`
- `teacher_payments`
- `fee_structures`
- `fee_payments`
- `student_attendance`
- `teacher_attendance`
- `audit_logs`

## Key Rules

- UUID primary keys
- Soft delete on users, students, teachers
- Student ID is not unique
- Audit log is immutable
- Closed academic years are read-only
- Fee payments are immutable
- Historical records preserved via `student_academic_records`
