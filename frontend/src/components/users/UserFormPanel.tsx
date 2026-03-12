import type { FormEvent } from "react";

import { Panel } from "../Panel";
import type {
  AccessOption,
  EmailLinkPreview,
  LoginMode,
  PermissionCode,
  Teacher,
  UserAccessOptions,
  UserRole,
} from "../../types";
import { assignmentLabel } from "./userHelpers";

interface UserFormValue {
  username: string;
  password: string;
  email: string;
  login_mode: LoginMode;
  role: UserRole;
  active: boolean;
  teacher_id: string;
  permissions: PermissionCode[];
}

interface UserFormPanelProps {
  accessOptions: UserAccessOptions;
  availablePermissions: AccessOption[];
  availableTeachers: Teacher[];
  emailLinkPreview: EmailLinkPreview | null;
  message: string;
  selectedTeacher: Teacher | null;
  submitting: boolean;
  teacherSearch: string;
  userForm: UserFormValue;
  onPermissionToggle: (code: PermissionCode) => void;
  onRoleChange: (role: UserRole) => void;
  onSetTeacherSearch: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onUserFormChange: (updater: (current: UserFormValue) => UserFormValue) => void;
}

export function UserFormPanel({
  accessOptions,
  availablePermissions,
  availableTeachers,
  emailLinkPreview,
  message,
  selectedTeacher,
  submitting,
  teacherSearch,
  userForm,
  onPermissionToggle,
  onRoleChange,
  onSetTeacherSearch,
  onSubmit,
  onUserFormChange,
}: UserFormPanelProps) {
  return (
    <Panel
      title="Create user"
      subtitle="Email-linked users sign in only from a welcome or requested login link. Password users stay local and are created only when no email-linked sign-in is being used."
    >
      {message ? <div className="message-banner is-success">{message}</div> : null}

      {emailLinkPreview?.login_url ? (
        <div className="message-banner">
          <strong>Email-link preview ready.</strong>
          <div className="field-note">
            {emailLinkPreview.email || "Linked email"} can sign in with this URL until SMTP delivery is configured.
          </div>
          <div className="toolbar">
            <a className="ghost-button" href={emailLinkPreview.login_url} target="_blank" rel="noreferrer">
              Open login URL
            </a>
            <span className="field-note">{emailLinkPreview.login_url}</span>
          </div>
        </div>
      ) : null}

      <form className="field-stack" onSubmit={onSubmit}>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="user-username">Username</label>
            <input
              id="user-username"
              value={userForm.username}
              onChange={(event) => onUserFormChange((current) => ({ ...current, username: event.target.value }))}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="user-role">Role</label>
            <select id="user-role" value={userForm.role} onChange={(event) => onRoleChange(event.target.value as UserRole)}>
              <option value="ADMIN">ADMIN</option>
              <option value="TEACHER">TEACHER</option>
              <option value="DATA_ENTRY">DATA_ENTRY</option>
              <option value="SUPER_ADMIN">SUPER_ADMIN</option>
            </select>
          </div>

          <div className="field">
            <label htmlFor="user-login-mode">Sign-in method</label>
            <select
              id="user-login-mode"
              value={userForm.login_mode}
              onChange={(event) =>
                onUserFormChange((current) => ({
                  ...current,
                  login_mode: event.target.value as LoginMode,
                  password: event.target.value === "PASSWORD" ? current.password : "",
                  email: event.target.value === "EMAIL_LINK" ? current.email : "",
                }))
              }
              disabled={userForm.role === "SUPER_ADMIN"}
            >
              {accessOptions.login_modes.includes("PASSWORD") ? <option value="PASSWORD">Password login</option> : null}
              {accessOptions.login_modes.includes("EMAIL_LINK") ? <option value="EMAIL_LINK">Email link only</option> : null}
            </select>
          </div>

          <div className="field">
            <label htmlFor="user-active">Active</label>
            <select
              id="user-active"
              value={String(userForm.active)}
              onChange={(event) => onUserFormChange((current) => ({ ...current, active: event.target.value === "true" }))}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>

          {userForm.login_mode === "PASSWORD" ? (
            <div className="field field-span-2">
              <label htmlFor="user-password">Password</label>
              <input
                id="user-password"
                type="password"
                value={userForm.password}
                onChange={(event) => onUserFormChange((current) => ({ ...current, password: event.target.value }))}
                required
              />
            </div>
          ) : (
            <div className="field field-span-2">
              <label htmlFor="user-email">Login email</label>
              <input
                id="user-email"
                type="email"
                value={userForm.email}
                onChange={(event) => onUserFormChange((current) => ({ ...current, email: event.target.value }))}
                placeholder="staff.user@gmail.com"
                required
              />
            </div>
          )}
        </div>

        {userForm.role === "SUPER_ADMIN" ? (
          <div className="message-banner">Super Admin remains the backoffice role and stays on password login with full system access.</div>
        ) : null}

        {userForm.login_mode === "EMAIL_LINK" ? (
          <div className="message-banner">
            This user will not receive or manage a local password. They sign in only from a welcome or requested email
            login link.
          </div>
        ) : (
          <div className="message-banner">
            Use password login only for staff who will not be linked to an email-based sign-in flow.
          </div>
        )}

        {userForm.role === "TEACHER" ? (
          <>
            <div className="message-banner">
              A teacher-linked account inherits classroom scope from the teacher profile. Attendance and class-bound
              student work stay limited to the assigned class and section combinations.
            </div>

            <div className="form-grid">
              <div className="field field-span-2">
                <label htmlFor="user-teacher-search">Search teacher profile</label>
                <input
                  id="user-teacher-search"
                  value={teacherSearch}
                  onChange={(event) => onSetTeacherSearch(event.target.value)}
                  placeholder="Search by teacher name, phone, or assigned class"
                />
              </div>
              <div className="field field-span-2">
                <label htmlFor="user-teacher">Teacher profile</label>
                <select
                  id="user-teacher"
                  value={userForm.teacher_id}
                  onChange={(event) => onUserFormChange((current) => ({ ...current, teacher_id: event.target.value }))}
                  required
                >
                  <option value="">Select teacher profile</option>
                  {availableTeachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name} | {teacher.assignment_count || 0} assignment(s)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="detail-stack">
              <div>
                <span className="field-note">Selected teacher</span>
                <strong>{selectedTeacher?.name || "No teacher selected"}</strong>
              </div>
              <div>
                <span className="field-note">Phone</span>
                <strong>{selectedTeacher?.phone || "Not available"}</strong>
              </div>
              <div>
                <span className="field-note">Class access</span>
                <strong>{selectedTeacher ? assignmentLabel(selectedTeacher) : "Select a teacher profile"}</strong>
              </div>
            </div>
          </>
        ) : null}

        {userForm.role !== "SUPER_ADMIN" ? (
          <div className="field-stack">
            <div className="panel-head">
              <div>
                <h2>Least-privilege access</h2>
                <p>Start from the role defaults, then switch off anything this user does not need.</p>
              </div>
            </div>

            <div className="check-list">
              {availablePermissions.map((permission: AccessOption) => (
                <label className="check-item" key={permission.code}>
                  <input
                    type="checkbox"
                    checked={userForm.permissions.includes(permission.code)}
                    onChange={() => onPermissionToggle(permission.code)}
                  />
                  <div>
                    <strong>{permission.label}</strong>
                    <div className="field-note">{permission.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        ) : null}

        <div className="form-actions">
          <button className="accent-button" type="submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create user"}
          </button>
        </div>
      </form>
    </Panel>
  );
}
