import type { FormEvent } from "react";

import { DataTable } from "../DataTable";
import { MetricCard } from "../MetricCard";
import { Panel } from "../Panel";
import { formatCurrency, formatDate, fullName } from "../../lib/format";
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
} from "../../types";

export function DashboardHero({
  activeYear,
  role,
  studentCount,
}: {
  activeYear?: AcademicYear;
  role?: string;
  studentCount: number;
}) {
  return (
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
            <strong>{role?.replace(/_/g, " ")}</strong>
          </div>
          <div>
            <span className="field-note">Recent students shown</span>
            <strong>{studentCount}</strong>
          </div>
        </div>
      </article>

      <article className="hero-panel">
        <p className="eyebrow">Workspace note</p>
        <h3>
          {role === "TEACHER" ? "Classroom view enabled" : role === "DATA_ENTRY" ? "Operations entry mode" : "Administrative oversight"}
        </h3>
        <p className="page-copy">
          {role === "TEACHER"
            ? "Use student and attendance screens for roster and daily register work. Finance and audit remain hidden by design."
            : role === "DATA_ENTRY"
              ? "Student creation, fee collection, and attendance entries remain available. Governance reports stay restricted."
              : "This role can work across finance, teacher contracts, reports, and year-level administration."}
        </p>
      </article>
    </section>
  );
}

export function DashboardMetrics({
  auditSummary,
  canViewAudit,
  dashboardOverview,
  financeVisible,
  loading,
  teachers,
  students,
}: {
  auditSummary: AuditSummary | null;
  canViewAudit: boolean;
  dashboardOverview: DashboardOverview | null;
  financeVisible: boolean;
  loading: boolean;
  teachers: Teacher[];
  students: Paginated<StudentRecord>;
}) {
  return (
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
        detail={
          financeVisible ? `${dashboardOverview?.pending_students ?? 0} students still pending fees` : "Restricted outside admin roles"
        }
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
  );
}

export function DashboardInsights({
  canViewAudit,
  canViewFinance,
  financeTrend,
  pendingApprovals,
}: {
  canViewAudit: boolean;
  canViewFinance: boolean;
  financeTrend: MonthlyFinanceTrendPoint[];
  pendingApprovals: AuditLog[];
}) {
  if (!canViewFinance && !canViewAudit) {
    return null;
  }

  return (
    <section className="stack-grid">
      {canViewFinance ? (
        <Panel title="Finance pulse" subtitle="Current calendar-year trend of collections versus teacher payouts.">
          <DataTable
            rows={financeTrend}
            emptyMessage="No finance trend data available."
            columns={[
              { key: "month", label: "Month", render: (row) => row.label },
              { key: "fees", label: "Fees collected", render: (row) => formatCurrency(row.fee_collected) },
              { key: "payroll", label: "Teacher paid", render: (row) => formatCurrency(row.teacher_paid) },
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
              { key: "actor", label: "Actor", render: (row) => row.performed_by_username || row.performed_by || "System" },
              {
                key: "status",
                label: "Review",
                render: (row) => <div className="status-pill status-pending">{row.review_status.replace(/_/g, " ")}</div>,
              },
              { key: "when", label: "When", render: (row) => formatDate(row.performed_at) },
            ]}
          />
        </Panel>
      ) : null}
    </section>
  );
}

export function ReferenceStudioPanel({
  classes,
  className,
  onClassNameChange,
  onCreateClass,
  onCreateSection,
  onSectionFormChange,
  saving,
  sectionForm,
  sections,
  visibleSections,
}: {
  classes: ClassRoom[];
  className: string;
  onClassNameChange: (value: string) => void;
  onCreateClass: (event: FormEvent<HTMLFormElement>) => void;
  onCreateSection: (event: FormEvent<HTMLFormElement>) => void;
  onSectionFormChange: (updater: (current: { class_id: string; name: string }) => { class_id: string; name: string }) => void;
  saving: boolean;
  sectionForm: { class_id: string; name: string };
  sections: Section[];
  visibleSections: Section[];
}) {
  return (
    <Panel title="Reference studio" subtitle="Create classes and sections from the same control deck used to review the rest of the system state.">
      <div className="stack-grid compact-grid">
        <form className="field-stack" onSubmit={onCreateClass}>
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
              onChange={(event) => onClassNameChange(event.target.value)}
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

        <form className="field-stack" onSubmit={onCreateSection}>
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
                onChange={(event) => onSectionFormChange((current) => ({ ...current, class_id: event.target.value }))}
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
                onChange={(event) => onSectionFormChange((current) => ({ ...current, name: event.target.value }))}
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
          <strong>{visibleSections.length ? visibleSections.map((section) => section.name).join(", ") : "Select a class to preview sections"}</strong>
        </div>
      </div>
    </Panel>
  );
}

export function AcademicYearControlPanel({
  academicYears,
  canManageYears,
  onCreateAcademicYear,
  onYearFormChange,
  onYearStateChange,
  saving,
  yearForm,
}: {
  academicYears: AcademicYear[];
  canManageYears: boolean;
  onCreateAcademicYear: (event: FormEvent<HTMLFormElement>) => void;
  onYearFormChange: (updater: (current: { name: string; start_date: string; end_date: string }) => { name: string; start_date: string; end_date: string }) => void;
  onYearStateChange: (id: string, action: "activate" | "close") => void;
  saving: boolean;
  yearForm: { name: string; start_date: string; end_date: string };
}) {
  return (
    <Panel title="Academic year control" subtitle="Create new year windows here, then activate or close them from the live list.">
      {canManageYears ? (
        <form className="field-stack" onSubmit={onCreateAcademicYear}>
          <div className="form-grid">
            <div className="field field-span-2">
              <label htmlFor="dashboard-year-name">Academic year name</label>
              <input
                id="dashboard-year-name"
                value={yearForm.name}
                onChange={(event) => onYearFormChange((current) => ({ ...current, name: event.target.value }))}
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
                onChange={(event) => onYearFormChange((current) => ({ ...current, start_date: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="dashboard-year-end">End date</label>
              <input
                id="dashboard-year-end"
                type="date"
                value={yearForm.end_date}
                onChange={(event) => onYearFormChange((current) => ({ ...current, end_date: event.target.value }))}
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
                  <button className="ghost-button" type="button" disabled={saving} onClick={() => onYearStateChange(year.id, "activate")}>
                    Activate
                  </button>
                ) : null}
                {canManageYears && !year.is_closed ? (
                  <button className="ghost-button" type="button" disabled={saving || year.is_closed} onClick={() => onYearStateChange(year.id, "close")}>
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
  );
}

export function DashboardLists({ academicYears, students }: { academicYears: AcademicYear[]; students: Paginated<StudentRecord> }) {
  return (
    <section className="stack-grid">
      <Panel title="Recent students" subtitle="Latest roster rows returned by the backend">
        <div className="list-card">
          {students.data.length ? (
            students.data.map((student) => (
              <div className="list-row" key={student.id}>
                <div>
                  <strong>{fullName(student.first_name, student.last_name)}</strong>
                  <span className="field-note">
                    {student.student_id || "Pending ID"} | {student.class_name || "No class"} / {student.section_name || "No section"}
                  </span>
                </div>
                <div className={`status-pill status-${student.status.toLowerCase().replace("_", "")}`}>{student.status.replace(/_/g, " ")}</div>
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
  );
}
