import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type {
  AccessOption,
  EmailLinkPreview,
  LoginMode,
  Paginated,
  PermissionCode,
  Teacher,
  UserAccessOptions,
  UserCreateResponse,
  UserRecord,
  UserRole,
} from "../types";

const emptyPage: Paginated<UserRecord> = {
  page: 1,
  size: 20,
  total_records: 0,
  total_pages: 0,
  data: [],
};

const emptyAccessOptions: UserAccessOptions = {
  permissions: [],
  default_permissions_by_role: {
    SUPER_ADMIN: [],
    ADMIN: [],
    TEACHER: [],
    DATA_ENTRY: [],
  },
  login_modes: ["PASSWORD", "EMAIL_LINK"],
};

function buildEmptyUserForm(options: UserAccessOptions) {
  return {
    username: "",
    password: "",
    email: "",
    login_mode: "PASSWORD" as LoginMode,
    role: "ADMIN" as UserRole,
    active: true,
    teacher_id: "",
    permissions: [...(options.default_permissions_by_role.ADMIN || [])] as PermissionCode[],
  };
}

function assignmentLabel(teacher: Teacher) {
  if (!teacher.assignments?.length) {
    return "No class assignment";
  }
  return teacher.assignments
    .map((assignment) => `${assignment.class_name || "Class"}${assignment.section_name ? ` / ${assignment.section_name}` : ""}`)
    .join(", ");
}

function loginModeLabel(value: LoginMode) {
  return value === "EMAIL_LINK" ? "Email link only" : "Password login";
}

export function UsersPage() {
  const { session, logout } = useAuth();
  const [users, setUsers] = useState<Paginated<UserRecord>>(emptyPage);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [accessOptions, setAccessOptions] = useState<UserAccessOptions>(emptyAccessOptions);
  const [userForm, setUserForm] = useState(() => buildEmptyUserForm(emptyAccessOptions));
  const [teacherSearch, setTeacherSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [emailLinkPreview, setEmailLinkPreview] = useState<EmailLinkPreview | null>(null);

  const permissionLabels = useMemo(
    () => Object.fromEntries(accessOptions.permissions.map((item) => [item.code, item.label])),
    [accessOptions.permissions],
  );

  const defaultPermissionsForRole = (role: UserRole) => accessOptions.default_permissions_by_role[role] || [];

  async function loadData() {
    if (!session) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const [userPage, teacherList, accessData] = await Promise.all([
        apiRequest<Paginated<UserRecord>>(`/users?page=${users.page}&size=${users.size}`, {
          token: session.accessToken,
        }),
        apiRequest<Teacher[]>("/teachers", {
          token: session.accessToken,
        }),
        apiRequest<UserAccessOptions>("/users/access-options", {
          token: session.accessToken,
        }),
      ]);
      setUsers(userPage);
      setTeachers(teacherList);
      setAccessOptions(accessData);
      setUserForm((current) =>
        current.permissions.length || current.username || current.email || current.teacher_id
          ? current
          : buildEmptyUserForm(accessData),
      );
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [session, users.page, users.size]);

  const linkedTeacherIds = new Set(users.data.map((user) => user.teacher_id).filter(Boolean));
  const availableTeachers = teachers.filter((teacher) => {
    if (linkedTeacherIds.has(teacher.id) && teacher.id !== userForm.teacher_id) {
      return false;
    }
    const term = teacherSearch.trim().toLowerCase();
    if (!term) {
      return true;
    }
    return `${teacher.name} ${teacher.phone || ""} ${assignmentLabel(teacher)}`.toLowerCase().includes(term);
  });
  const selectedTeacher = teachers.find((teacher) => teacher.id === userForm.teacher_id) || null;

  const availablePermissions = accessOptions.permissions.filter((item) =>
    defaultPermissionsForRole(userForm.role).includes(item.code),
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");
    setEmailLinkPreview(null);

    try {
      const response = await apiRequest<UserCreateResponse>("/users", {
        method: "POST",
        token: session.accessToken,
        body: {
          username: userForm.username,
          password: userForm.login_mode === "PASSWORD" ? userForm.password : null,
          email: userForm.login_mode === "EMAIL_LINK" ? userForm.email || null : null,
          login_mode: userForm.login_mode,
          role: userForm.role,
          active: userForm.active,
          teacher_id: userForm.role === "TEACHER" ? userForm.teacher_id || null : null,
          permissions: userForm.role === "SUPER_ADMIN" ? [] : userForm.permissions,
        },
      });
      setMessage(
        userForm.login_mode === "EMAIL_LINK"
          ? "Email-link account created. A welcome login URL is ready below for manual sharing until mail delivery is configured."
          : "Password-based user created successfully.",
      );
      setEmailLinkPreview(response.email_link);
      setUserForm(buildEmptyUserForm(accessOptions));
      setTeacherSearch("");
      await loadData();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  function handleRoleChange(nextRole: UserRole) {
    setUserForm((current) => ({
      ...current,
      role: nextRole,
      teacher_id: nextRole === "TEACHER" ? current.teacher_id : "",
      login_mode: nextRole === "SUPER_ADMIN" ? "PASSWORD" : current.login_mode,
      permissions: [...defaultPermissionsForRole(nextRole)],
    }));
  }

  function handlePermissionToggle(code: PermissionCode) {
    setUserForm((current) => {
      const hasPermission = current.permissions.includes(code);
      return {
        ...current,
        permissions: hasPermission
          ? current.permissions.filter((item) => item !== code)
          : [...current.permissions, code],
      };
    });
  }

  return (
    <>
      <PageIntro
        eyebrow="Identity and access"
        title="Users"
        description="Super Admin runs the backoffice here: choose password login or email-link-only sign-in, then narrow each user down to the least access they need. Teacher classroom scope still comes from the linked teacher profile and that teacher’s class assignments."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
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

      <section className="split-grid">
        <Panel
          title="Create user"
          subtitle="Email-linked users sign in only from a welcome or requested login link. Password users stay local and are created only when no email-linked sign-in is being used."
        >
          <form className="field-stack" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="user-username">Username</label>
                <input
                  id="user-username"
                  value={userForm.username}
                  onChange={(event) => setUserForm((current) => ({ ...current, username: event.target.value }))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="user-role">Role</label>
                <select id="user-role" value={userForm.role} onChange={(event) => handleRoleChange(event.target.value as UserRole)}>
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
                    setUserForm((current) => ({
                      ...current,
                      login_mode: event.target.value as LoginMode,
                      password: event.target.value === "PASSWORD" ? current.password : "",
                      email: event.target.value === "EMAIL_LINK" ? current.email : "",
                    }))
                  }
                  disabled={userForm.role === "SUPER_ADMIN"}
                >
                  <option value="PASSWORD">Password login</option>
                  <option value="EMAIL_LINK">Email link only</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="user-active">Active</label>
                <select
                  id="user-active"
                  value={String(userForm.active)}
                  onChange={(event) =>
                    setUserForm((current) => ({ ...current, active: event.target.value === "true" }))
                  }
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
                    onChange={(event) => setUserForm((current) => ({ ...current, password: event.target.value }))}
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
                    onChange={(event) => setUserForm((current) => ({ ...current, email: event.target.value }))}
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
                      onChange={(event) => setTeacherSearch(event.target.value)}
                      placeholder="Search by teacher name, phone, or assigned class"
                    />
                  </div>
                  <div className="field field-span-2">
                    <label htmlFor="user-teacher">Teacher profile</label>
                    <select
                      id="user-teacher"
                      value={userForm.teacher_id}
                      onChange={(event) => setUserForm((current) => ({ ...current, teacher_id: event.target.value }))}
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
                        onChange={() => handlePermissionToggle(permission.code)}
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

        <Panel
          title="User directory"
          subtitle="Auth mode, teacher link, and explicit permissions are shown together so backoffice can review who can access what."
        >
          <DataTable
            rows={users.data}
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
              {
                key: "role",
                label: "Role",
                render: (row) => row.role,
              },
              {
                key: "login_mode",
                label: "Sign-in",
                render: (row) => loginModeLabel(row.login_mode),
              },
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
                    ? row.permissions.map((permission) => permissionLabels[permission] || permission).join(", ")
                    : "No explicit access",
              },
            ]}
          />

          <div className="toolbar">
            <button
              className="ghost-button"
              type="button"
              disabled={users.page <= 1}
              onClick={() => setUsers((current) => ({ ...current, page: current.page - 1 }))}
            >
              Previous
            </button>
            <span className="field-note">
              Page {users.page} of {Math.max(users.total_pages, 1)}
            </span>
            <button
              className="ghost-button"
              type="button"
              disabled={users.page >= Math.max(users.total_pages, 1)}
              onClick={() => setUsers((current) => ({ ...current, page: current.page + 1 }))}
            >
              Next
            </button>
          </div>
        </Panel>
      </section>
    </>
  );
}
