import { formatDate, fullName } from "../../lib/format";
import type { StudentRecord } from "../../types";

export function buildStudentColumns({
  canManageStudents,
  onEdit,
  onToggleStudentSelection,
  selectedStudents,
}: {
  canManageStudents: boolean;
  onEdit: (student: StudentRecord) => void;
  onToggleStudentSelection: (studentId: string) => void;
  selectedStudents: string[];
}) {
  return [
    {
      key: "select",
      label: "",
      render: (row: StudentRecord) => (
        <input type="checkbox" checked={selectedStudents.includes(row.id)} onChange={() => onToggleStudentSelection(row.id)} />
      ),
    },
    {
      key: "student",
      label: "Student",
      render: (row: StudentRecord) => (
        <div>
          <strong>{fullName(row.first_name, row.last_name)}</strong>
          <div className="field-note">{row.student_id || "Student ID pending"}</div>
        </div>
      ),
    },
    {
      key: "class",
      label: "Placement",
      render: (row: StudentRecord) => (
        <div>
          <strong>{row.class_name || "No class"}</strong>
          <div className="field-note">{row.section_name || "No section"}</div>
        </div>
      ),
    },
    {
      key: "guardian",
      label: "Guardian",
      render: (row: StudentRecord) => (
        <div>
          <strong>{row.guardian_name || "Not set"}</strong>
          <div className="field-note">{row.guardian_phone || "No phone"}</div>
        </div>
      ),
    },
    {
      key: "dob",
      label: "DOB",
      render: (row: StudentRecord) => formatDate(row.dob),
    },
    {
      key: "status",
      label: "Status",
      render: (row: StudentRecord) => (
        <div className={`status-pill status-${row.status.toLowerCase().replace("_", "")}`}>{row.status.replace(/_/g, " ")}</div>
      ),
    },
    {
      key: "actions",
      label: "Actions",
      render: (row: StudentRecord) =>
        canManageStudents ? (
          <button className="ghost-button" type="button" onClick={() => onEdit(row)}>
            Edit
          </button>
        ) : (
          <span className="field-note">Read only</span>
        ),
    },
  ];
}
