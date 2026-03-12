import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { PageIntro } from "../components/PageIntro";
import { UserDirectoryPanel } from "../components/users/UserDirectoryPanel";
import { UserFormPanel } from "../components/users/UserFormPanel";
import { assignmentLabel, buildEmptyUserForm } from "../components/users/userHelpers";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type {
  EmailLinkPreview,
  Paginated,
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

  function handlePermissionToggle(code: (typeof userForm.permissions)[number]) {
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
        description="Super Admin runs the backoffice here: choose password login or email-link-only sign-in, then narrow each user down to the least access they need. Teacher classroom scope still comes from the linked teacher profile and that teacher's class assignments."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}

      <section className="split-grid">
        <UserFormPanel
          accessOptions={accessOptions}
          availablePermissions={availablePermissions}
          availableTeachers={availableTeachers}
          emailLinkPreview={emailLinkPreview}
          message={message}
          selectedTeacher={selectedTeacher}
          submitting={submitting}
          teacherSearch={teacherSearch}
          userForm={userForm}
          onPermissionToggle={handlePermissionToggle}
          onRoleChange={handleRoleChange}
          onSetTeacherSearch={setTeacherSearch}
          onSubmit={handleSubmit}
          onUserFormChange={setUserForm}
        />
        <UserDirectoryPanel
          loading={loading}
          page={users}
          permissionLabels={permissionLabels}
          onPageChange={(page) => setUsers((current) => ({ ...current, page }))}
        />
      </section>
    </>
  );
}
