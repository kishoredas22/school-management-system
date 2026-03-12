import type { Teacher } from "../../types";

export const emptyTeacherForm = {
  name: "",
  phone: "",
  email: "",
  is_active: true,
};

export const emptyAssignmentDraft = {
  class_id: "",
  section_id: "",
  academic_year_id: "",
};

export const emptyContractForm = {
  teacher_id: "",
  academic_year_id: "",
  yearly_contract_amount: "",
  monthly_salary: "",
};

export function deriveMonthlySalary(value: string) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount <= 0) {
    return "";
  }
  return (amount / 12).toFixed(2);
}

export function assignmentText(teacher: Teacher) {
  if (!teacher.assignments?.length) {
    return "No classroom assignments";
  }
  return teacher.assignments
    .map((assignment) => `${assignment.class_name || "Class"}${assignment.section_name ? ` / ${assignment.section_name}` : ""}`)
    .join(", ");
}
