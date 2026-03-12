# Implementation Notes

## Source Gaps Resolved Conservatively

### Teacher account linkage

The source documents define teacher-specific login behavior and teacher-specific access restrictions, but they do not define how `users` map to `teachers`. This implementation adds an internal optional `users.teacher_id` foreign key so teacher JWTs can be constrained to assigned classes.

### Teacher assigned classes persistence

The source documents require editable assigned classes and teacher-only access to assigned classes, but they do not define a storage table. This implementation adds an internal `teacher_class_assignments` table.

### Promotion class progression

The source documents define the promotion workflow but do not define class ordering or a target-class mapping strategy. To avoid inventing undocumented behavior, promotion preserves the current class and section while creating the next-year academic record. If the class progression rule is clarified later, that logic belongs in `app/services/promotion_service.py`.
