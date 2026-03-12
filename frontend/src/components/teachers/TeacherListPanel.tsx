import { DataTable } from "../DataTable";
import { Panel } from "../Panel";
import { assignmentText } from "./teacherHelpers";
import type { Teacher } from "../../types";

export function TeacherListPanel({
  teachers,
  loading,
  onOpenDetail,
  onEdit,
}: {
  teachers: Teacher[];
  loading: boolean;
  onOpenDetail: (teacherId: string) => void;
  onEdit: (teacher: Teacher) => void;
}) {
  return (
    <Panel title="Faculty list" subtitle="Teacher records now surface classroom assignments alongside the basic profile.">
      <DataTable
        rows={teachers}
        emptyMessage={loading ? "Loading teachers..." : "No teachers found."}
        columns={[
          {
            key: "teacher",
            label: "Teacher",
            render: (row: Teacher) => (
              <div>
                <button className="link-button" type="button" onClick={() => onOpenDetail(row.id)}>
                  {row.name}
                </button>
                <div className="field-note">{row.email || row.phone || "No contact on file"}</div>
                <div className="field-note">Click name or view detail to open the full teacher profile page.</div>
              </div>
            ),
          },
          {
            key: "assignments",
            label: "Assignments",
            render: (row: Teacher) => assignmentText(row),
          },
          {
            key: "active",
            label: "Status",
            render: (row: Teacher) => (
              <div className={`status-pill ${row.is_active ? "status-active" : "status-inactive"}`}>
                {row.is_active ? "Active" : "Inactive"}
              </div>
            ),
          },
          {
            key: "action",
            label: "Action",
            render: (row: Teacher) => (
              <div className="table-action-stack">
                <button className="ghost-button" type="button" onClick={() => onOpenDetail(row.id)}>
                  View detail
                </button>
                <button className="ghost-button" type="button" onClick={() => onEdit(row)}>
                  Edit teacher
                </button>
              </div>
            ),
          },
        ]}
      />
    </Panel>
  );
}
