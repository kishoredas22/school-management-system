import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { MetricCard } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { hasPermission, useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatCurrency, formatDate, fullName } from "../lib/format";
import type {
  AcademicYear,
  AuditLog,
  AuditSummary,
  ClassRoom,
  DashboardOverview,
  MonthlyFinanceTrendPoint,
  Paginated,
  Section,
  StudentRecord,
  Teacher,
} from "../types";

const emptyYearForm = {
  name: "",
  start_date: "",
  end_date: "",
};

export function DashboardPage() {
  const { session, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [students, setStudents] = useState<Paginated<StudentRecord>>({
    page: 1,
    size: 20,
    total_records: 0,
    total_pages: 0,
    data: [],
  });
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [dashboardOverview, setDashboardOverview] = useState<DashboardOverview | null>(null);
  const [auditSummary, setAuditSummary] = useState<AuditSummary | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<AuditLog[]>([]);
  const [financeTrend, setFinanceTrend] = useState<MonthlyFinanceTrendPoint[]>([]);
  const [className, setClassName] = useState("");
  const [sectionForm, setSectionForm] = useState({ class_id: "", name: "" });
  const [yearForm, setYearForm] = useState(emptyYearForm);

  const canViewStudents = hasPermission(session, "STUDENT_RECORDS");
  const canViewTeachers = hasPermission(session, "TEACHER_MANAGE");
  const canViewFinance = hasPermission(session, "REPORT_VIEW");
  const canViewAudit = hasPermission(session, "AUDIT_VIEW");
  const canManageReferences = hasPermission(session, "REFERENCE_MANAGE");
  const canManageYears = session?.role === "SUPER_ADMIN";

  async function loadDashboard() {
    if (!session) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const yearsPromise = apiRequest<AcademicYear[]>("/academic-years", { token: session.accessToken });
      const studentsPromise = canViewStudents
        ? apiRequest<Paginated<StudentRecord>>("/students?page=1&size=8&include_inactive=true", {
            token: session.accessToken,
          })
        : Promise.resolve({
            page: 1,
            size: 8,
            total_records: 0,
            total_pages: 0,
            data: [],
          });
      const teachersPromise = canViewTeachers
        ? apiRequest<Teacher[]>("/teachers", { token: session.accessToken })
        : Promise.resolve([]);
      const dashboardPromise = canViewFinance
        ? apiRequest<DashboardOverview>("/reports/dashboard", { token: session.accessToken })
        : Promise.resolve(null);
      const trendPromise = canViewFinance
        ? apiRequest<MonthlyFinanceTrendPoint[]>(`/reports/finance/trend?calendar_year=${new Date().getFullYear()}`, {
            token: session.accessToken,
          })
        : Promise.resolve([]);
      const classesPromise = canManageReferences
        ? apiRequest<ClassRoom[]>("/reference/classes", { token: session.accessToken })
        : Promise.resolve([]);
      const sectionsPromise = canManageReferences
        ? apiRequest<Section[]>("/reference/sections", { token: session.accessToken })
        : Promise.resolve([]);
      const auditSummaryPromise = canViewAudit
        ? apiRequest<AuditSummary>("/audit-logs/summary", { token: session.accessToken })
        : Promise.resolve(null);
      const pendingApprovalsPromise = canViewAudit
        ? apiRequest<Paginated<AuditLog>>("/audit-logs?review_status=PENDING&page=1&size=5", {
            token: session.accessToken,
          })
        : Promise.resolve({
            page: 1,
            size: 5,
            total_records: 0,
            total_pages: 0,
            data: [],
          });

      const [years, studentPage, teacherList, dashboardData, trendData, classList, sectionList, auditData, pendingData] =
        await Promise.all([
        yearsPromise,
        studentsPromise,
        teachersPromise,
        dashboardPromise,
        trendPromise,
        classesPromise,
        sectionsPromise,
        auditSummaryPromise,
        pendingApprovalsPromise,
      ]);

      setAcademicYears(years);
      setStudents(studentPage);
      setTeachers(teacherList);
      setDashboardOverview(dashboardData);
      setFinanceTrend(trendData);
      setClasses(classList);
      setSections(sectionList);
      setAuditSummary(auditData);
      setPendingApprovals(pendingData.data);
      setSectionForm((current) => ({
        ...current,
        class_id: current.class_id || classList[0]?.id || "",
      }));
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
    loadDashboard();
  }, [canManageReferences, canViewAudit, canViewFinance, canViewStudents, canViewTeachers, session]);

  const activeYear = academicYears.find((item) => item.is_active) || academicYears[0];
  const financeVisible = Boolean(dashboardOverview);
  const visibleSections = sections.filter((section) => !sectionForm.class_id || section.class_id === sectionForm.class_id);

  async function handleCreateClass(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/reference/classes", {
        method: "POST",
        token: session.accessToken,
        body: { name: className },
      });
      setMessage("Class created.");
      setClassName("");
      await loadDashboard();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateSection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/reference/sections", {
        method: "POST",
        token: session.accessToken,
        body: sectionForm,
      });
      setMessage("Section created.");
      setSectionForm((current) => ({ ...current, name: "" }));
      await loadDashboard();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateAcademicYear(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/academic-years", {
        method: "POST",
        token: session.accessToken,
        body: yearForm,
      });
      setMessage("Academic year created.");
      setYearForm(emptyYearForm);
      await loadDashboard();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSaving(false);
    }
  }

  async function changeAcademicYearState(academicYearId: string, action: "activate" | "close") {
    if (!session) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/academic-years/${academicYearId}/${action}`, {
        method: "PUT",
        token: session.accessToken,
      });
      setMessage(`Academic year ${action}d.`);
      await loadDashboard();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageIntro
        eyebrow="Operations Dashboard"
        title="School pulse"
        description="A role-aware command surface for current academic activity, quick counts, and operational setup. Admin tools for classes, sections, and academic years live here."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="hero-strip">
        <article className="hero-panel">
          <p className="eyebrow">Current context</p>
          <h3>{activeYear ? activeYear.name : "No academic year available"}</h3>
          <p className="page-copy">
            {activeYear
              ? `The active cycle runs from ${formatDate(activeYear.start_date)} to ${formatDate(activeYear.end_date)}.`
              : "Create or activate an academic year to anchor student, fee, contract, and attendance records."}
          </p>
          <div className="detail-stack">
            <div>
              <span className="field-note">Closed</span>
              <strong>{activeYear?.is_closed ? "Yes" : "No"}</strong>
            </div>
            <div>
              <span className="field-note">Visible role</span>
              <strong>{session?.role.replace(/_/g, " ")}</strong>
            </div>
            <div>
              <span className="field-note">Recent students shown</span>
              <strong>{students.data.length}</strong>
            </div>
          </div>
        </article>

        <article className="hero-panel">
          <p className="eyebrow">Workspace note</p>
          <h3>
            {session?.role === "TEACHER"
              ? "Classroom view enabled"
              : session?.role === "DATA_ENTRY"
                ? "Operations entry mode"
                : "Administrative oversight"}
          </h3>
          <p className="page-copy">
            {session?.role === "TEACHER"
              ? "Use student and attendance screens for roster and daily register work. Finance and audit remain hidden by design."
              : session?.role === "DATA_ENTRY"
                ? "Student creation, fee collection, and attendance entries remain available. Governance reports stay restricted."
                : "This role can work across finance, teacher contracts, reports, and year-level administration."}
          </p>
        </article>
      </section>

      <section className="metric-grid">
        <MetricCard
          label="Students tracked"
          value={loading ? "..." : String(dashboardOverview?.student_total ?? students.total_records)}
          detail={`${dashboardOverview?.active_students ?? students.data.length} active students in the current scope`}
          tone="sand"
        />
        <MetricCard
          label="Teachers visible"
          value={loading ? "..." : String(dashboardOverview?.teacher_total ?? teachers.length)}
          detail={financeVisible ? "Faculty list available to admin roles" : "Role-limited data for current user"}
          tone="mint"
        />
        <MetricCard
          label="Fees collected"
          value={loading ? "..." : formatCurrency(dashboardOverview?.fee_collected ?? 0)}
          detail={financeVisible ? `${dashboardOverview?.pending_students ?? 0} students still pending fees` : "Restricted outside admin roles"}
          tone="ink"
        />
        <MetricCard
          label={canViewAudit ? "Approvals pending" : "Salary pending"}
          value={loading ? "..." : canViewAudit ? String(auditSummary?.pending_reviews ?? 0) : formatCurrency(dashboardOverview?.salary_pending ?? 0)}
          detail={
            canViewAudit
              ? `${auditSummary?.review_required ?? 0} events marked for governance review`
              : financeVisible
                ? "Open balance across teacher contracts"
                : "Restricted outside admin roles"
          }
          tone="coral"
        />
      </section>

      {(canViewFinance || canViewAudit) ? (
        <section className="stack-grid">
          {canViewFinance ? (
            <Panel title="Finance pulse" subtitle="Current calendar-year trend of collections versus teacher payouts.">
              <DataTable
                rows={financeTrend}
                emptyMessage="No finance trend data available."
                columns={[
                  {
                    key: "month",
                    label: "Month",
                    render: (row) => row.label,
                  },
                  {
                    key: "fees",
                    label: "Fees collected",
                    render: (row) => formatCurrency(row.fee_collected),
                  },
                  {
                    key: "payroll",
                    label: "Teacher paid",
                    render: (row) => formatCurrency(row.teacher_paid),
                  },
                ]}
              />
            </Panel>
          ) : null}

          {canViewAudit ? (
            <Panel title="Governance queue" subtitle="Recent events waiting for Super Admin review.">
              <DataTable
                rows={pendingApprovals}
                emptyMessage="No approval reviews are waiting right now."
                columns={[
                  {
                    key: "entity",
                    label: "Entity",
                    render: (row) => (
                      <div>
                        <strong>{row.entity_name}</strong>
                        <div className="field-note">{row.action}</div>
                      </div>
                    ),
                  },
                  {
                    key: "actor",
                    label: "Actor",
                    render: (row) => row.performed_by_username || row.performed_by || "System",
                  },
                  {
                    key: "status",
                    label: "Review",
                    render: (row) => <div className="status-pill status-pending">{row.review_status.replace(/_/g, " ")}</div>,
                  },
                  {
                    key: "when",
                    label: "When",
                    render: (row) => formatDate(row.performed_at),
                  },
                ]}
              />
            </Panel>
          ) : null}
        </section>
      ) : null}

      {canManageReferences ? (
        <section className="stack-grid">
          <Panel title="Reference studio" subtitle="Create classes and sections from the same control deck used to review the rest of the system state.">
            <div className="stack-grid compact-grid">
              <form className="field-stack" onSubmit={handleCreateClass}>
                <div className="panel-head">
                  <div>
                    <h2>Create class</h2>
                    <p>Classes become available immediately in students, fees, teachers, and attendance.</p>
                  </div>
                </div>
                <div className="field">
                  <label htmlFor="dashboard-class-name">Class name</label>
                  <input
                    id="dashboard-class-name"
                    value={className}
                    onChange={(event) => setClassName(event.target.value)}
                    placeholder="Example: Class 10"
                    required
                  />
                </div>
                <div className="form-actions">
                  <button className="accent-button" type="submit" disabled={saving}>
                    Create class
                  </button>
                </div>
              </form>

              <form className="field-stack" onSubmit={handleCreateSection}>
                <div className="panel-head">
                  <div>
                    <h2>Create section</h2>
                    <p>Sections are created within a class so teacher access and student placement stay consistent.</p>
                  </div>
                </div>
                <div className="form-grid">
                  <div className="field">
                    <label htmlFor="dashboard-section-class">Class</label>
                    <select
                      id="dashboard-section-class"
                      value={sectionForm.class_id}
                      onChange={(event) => setSectionForm((current) => ({ ...current, class_id: event.target.value }))}
                      required
                    >
                      <option value="">Select class</option>
                      {classes.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label htmlFor="dashboard-section-name">Section name</label>
                    <input
                      id="dashboard-section-name"
                      value={sectionForm.name}
                      onChange={(event) => setSectionForm((current) => ({ ...current, name: event.target.value }))}
                      placeholder="Example: A"
                      required
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button className="accent-button" type="submit" disabled={saving}>
                    Create section
                  </button>
                </div>
              </form>
            </div>

            <div className="detail-stack">
              <div>
                <span className="field-note">Classes</span>
                <strong>{classes.length}</strong>
              </div>
              <div>
                <span className="field-note">Sections</span>
                <strong>{sections.length}</strong>
              </div>
              <div>
                <span className="field-note">Current section context</span>
                <strong>
                  {visibleSections.length
                    ? visibleSections.map((section) => section.name).join(", ")
                    : "Select a class to preview sections"}
                </strong>
              </div>
            </div>
          </Panel>

          <Panel title="Academic year control" subtitle="Create new year windows here, then activate or close them from the live list.">
            {canManageYears ? (
              <form className="field-stack" onSubmit={handleCreateAcademicYear}>
                <div className="form-grid">
                  <div className="field field-span-2">
                    <label htmlFor="dashboard-year-name">Academic year name</label>
                    <input
                      id="dashboard-year-name"
                      value={yearForm.name}
                      onChange={(event) => setYearForm((current) => ({ ...current, name: event.target.value }))}
                      placeholder="Example: 2026-2027"
                      required
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="dashboard-year-start">Start date</label>
                    <input
                      id="dashboard-year-start"
                      type="date"
                      value={yearForm.start_date}
                      onChange={(event) => setYearForm((current) => ({ ...current, start_date: event.target.value }))}
                      required
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="dashboard-year-end">End date</label>
                    <input
                      id="dashboard-year-end"
                      type="date"
                      value={yearForm.end_date}
                      onChange={(event) => setYearForm((current) => ({ ...current, end_date: event.target.value }))}
                      required
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button className="accent-button" type="submit" disabled={saving}>
                    Create academic year
                  </button>
                </div>
              </form>
            ) : (
              <div className="message-banner">Only Super Admin can create, activate, or close academic years.</div>
            )}

            <div className="list-card">
              {academicYears.length ? (
                academicYears.map((year) => (
                  <div className="list-row" key={year.id}>
                    <div>
                      <strong>{year.name}</strong>
                      <span className="field-note">
                        {formatDate(year.start_date)} to {formatDate(year.end_date)}
                      </span>
                    </div>
                    <div className="toolbar">
                      <div className={`status-pill ${year.is_closed ? "status-closed" : year.is_active ? "status-active" : "status-pending"}`}>
                        {year.is_closed ? "Closed" : year.is_active ? "Active" : "Open"}
                      </div>
                      {canManageYears && !year.is_closed && !year.is_active ? (
                        <button className="ghost-button" type="button" disabled={saving} onClick={() => changeAcademicYearState(year.id, "activate")}>
                          Activate
                        </button>
                      ) : null}
                      {canManageYears && !year.is_closed ? (
                        <button className="ghost-button" type="button" disabled={saving || year.is_closed} onClick={() => changeAcademicYearState(year.id, "close")}>
                          Close
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">No academic years found.</div>
              )}
            </div>
          </Panel>
        </section>
      ) : null}

      <section className="stack-grid">
        <Panel title="Recent students" subtitle="Latest roster rows returned by the backend">
          <div className="list-card">
            {students.data.length ? (
              students.data.map((student) => (
                <div className="list-row" key={student.id}>
                  <div>
                    <strong>{fullName(student.first_name, student.last_name)}</strong>
                    <span className="field-note">
                      {student.student_id || "Pending ID"} | {student.class_name || "No class"} /{" "}
                      {student.section_name || "No section"}
                    </span>
                  </div>
                  <div className={`status-pill status-${student.status.toLowerCase().replace("_", "")}`}>
                    {student.status.replace(/_/g, " ")}
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">No student rows available yet.</div>
            )}
          </div>
        </Panel>

        <Panel title="Academic years" subtitle="Year windows currently stored in the system">
          <div className="list-card">
            {academicYears.length ? (
              academicYears.map((year) => (
                <div className="list-row" key={year.id}>
                  <div>
                    <strong>{year.name}</strong>
                    <span className="field-note">
                      {formatDate(year.start_date)} to {formatDate(year.end_date)}
                    </span>
                  </div>
                  <div className={`status-pill ${year.is_closed ? "status-closed" : year.is_active ? "status-active" : "status-pending"}`}>
                    {year.is_closed ? "Closed" : year.is_active ? "Active" : "Open"}
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">No academic years found.</div>
            )}
          </div>
        </Panel>
      </section>
    </>
  );
}
