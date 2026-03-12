import type { LoginMode, Teacher, UserAccessOptions, UserRole } from "../../types";

export function buildEmptyUserForm(options: UserAccessOptions) {
  return {
    username: "",
    password: "",
    email: "",
    login_mode: "PASSWORD" as LoginMode,
    role: "ADMIN" as UserRole,
    active: true,
    teacher_id: "",
    permissions: [...(options.default_permissions_by_role.ADMIN || [])],
  };
}

export function assignmentLabel(teacher: Teacher) {
  if (!teacher.assignments?.length) {
    return "No class assignment";
  }
  return teacher.assignments
    .map((assignment) => `${assignment.class_name || "Class"}${assignment.section_name ? ` / ${assignment.section_name}` : ""}`)
    .join(", ");
}

export function loginModeLabel(value: LoginMode) {
  return value === "EMAIL_LINK" ? "Email link only" : "Password login";
}
