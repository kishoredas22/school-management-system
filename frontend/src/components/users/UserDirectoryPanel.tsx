import { DataTable } from "../DataTable";
import { Panel } from "../Panel";
import type { Paginated, PermissionCode, UserRecord } from "../../types";
import { loginModeLabel } from "./userHelpers";

interface UserDirectoryPanelProps {
  loading: boolean;
  page: Paginated<UserRecord>;
  permissionLabels: Record<string, string>;
  onPageChange: (page: number) => void;
}

export function UserDirectoryPanel({ loading, page, permissionLabels, onPageChange }: UserDirectoryPanelProps) {
  return (
    <Panel
      title="User directory"
      subtitle="Auth mode, teacher link, and explicit permissions are shown together so backoffice can review who can access what."
    >
      <DataTable
        rows={page.data}
        emptyMessage={loading ? "Loading users..." : "No users created yet."}
        columns={[
          {
            key: "username",
            label: "User",
            render: (row) => (
              <div className="assignment-summary">
                <strong>{row.username}</strong>
                <div className="field-note">{row.email || "No email-linked sign-in"}</div>
              </div>
            ),
          },
          { key: "role", label: "Role", render: (row) => row.role },
          { key: "login_mode", label: "Sign-in", render: (row) => loginModeLabel(row.login_mode) },
          {
            key: "active",
            label: "Status",
            render: (row) => (
              <div className={`status-pill ${row.is_active ? "status-active" : "status-inactive"}`}>
                {row.is_active ? "Active" : "Inactive"}
              </div>
            ),
          },
          {
            key: "teacher",
            label: "Teacher link",
            render: (row) =>
              row.teacher_id ? (
                <div className="assignment-summary">
                  <strong>{row.teacher_name || "Teacher linked"}</strong>
                  <div className="field-note">{row.teacher_phone || "No phone on file"}</div>
                  <div className="field-note">
                    {row.teacher_assignment_count} assignment(s):{" "}
                    {row.teacher_assignments.length
                      ? row.teacher_assignments
                          .map(
                            (assignment) =>
                              `${assignment.class_name || "Class"}${assignment.section_name ? ` / ${assignment.section_name}` : ""}`,
                          )
                          .join(", ")
                      : "No classroom assignments"}
                  </div>
                </div>
              ) : (
                "Not linked"
              ),
          },
          {
            key: "permissions",
            label: "Access",
            render: (row) =>
              row.permissions.length
                ? row.permissions.map((permission: PermissionCode) => permissionLabels[permission] || permission).join(", ")
                : "No explicit access",
          },
        ]}
      />

      <div className="toolbar">
        <button className="ghost-button" type="button" disabled={page.page <= 1} onClick={() => onPageChange(page.page - 1)}>
          Previous
        </button>
        <span className="field-note">
          Page {page.page} of {Math.max(page.total_pages, 1)}
        </span>
        <button
          className="ghost-button"
          type="button"
          disabled={page.page >= Math.max(page.total_pages, 1)}
          onClick={() => onPageChange(page.page + 1)}
        >
          Next
        </button>
      </div>
    </Panel>
  );
}
