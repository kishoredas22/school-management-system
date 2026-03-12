import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  AcademicYearControlPanel,
  DashboardHero,
  DashboardInsights,
  DashboardLists,
  DashboardMetrics,
  ReferenceStudioPanel,
} from "../components/dashboard/DashboardPanels";
import { PageIntro } from "../components/PageIntro";
import { hasPermission, useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
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

      <DashboardHero activeYear={activeYear} role={session?.role} studentCount={students.data.length} />
      <DashboardMetrics
        auditSummary={auditSummary}
        canViewAudit={canViewAudit}
        dashboardOverview={dashboardOverview}
        financeVisible={financeVisible}
        loading={loading}
        teachers={teachers}
        students={students}
      />
      <DashboardInsights
        canViewAudit={canViewAudit}
        canViewFinance={canViewFinance}
        financeTrend={financeTrend}
        pendingApprovals={pendingApprovals}
      />

      {canManageReferences ? (
        <section className="stack-grid">
          <ReferenceStudioPanel
            classes={classes}
            className={className}
            onClassNameChange={setClassName}
            onCreateClass={handleCreateClass}
            onCreateSection={handleCreateSection}
            onSectionFormChange={setSectionForm}
            saving={saving}
            sectionForm={sectionForm}
            sections={sections}
            visibleSections={visibleSections}
          />
          <AcademicYearControlPanel
            academicYears={academicYears}
            canManageYears={canManageYears}
            onCreateAcademicYear={handleCreateAcademicYear}
            onYearFormChange={setYearForm}
            onYearStateChange={changeAcademicYearState}
            saving={saving}
            yearForm={yearForm}
          />
        </section>
      ) : null}

      <DashboardLists academicYears={academicYears} students={students} />
    </>
  );
}
