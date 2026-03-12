import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { PageIntro } from "../components/PageIntro";
import { StudentMaintenancePanel, StudentPromotionPanel } from "../components/students/StudentMaintenancePanel";
import { StudentRosterPanel } from "../components/students/StudentRosterPanel";
import { buildStudentColumns } from "../components/students/studentHelpers";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type {
  AcademicYear,
  ClassRoom,
  Paginated,
  PromotionAction,
  Section,
  StudentRecord,
  StudentStatus,
} from "../types";

const emptyPage: Paginated<StudentRecord> = {
  page: 1,
  size: 20,
  total_records: 0,
  total_pages: 0,
  data: [],
};

const emptyStudentForm = {
  student_id: "",
  first_name: "",
  last_name: "",
  dob: "",
  guardian_name: "",
  guardian_phone: "",
  class_id: "",
  section_id: "",
  academic_year_id: "",
};

const emptyPromotionForm = {
  academic_year_from: "",
  academic_year_to: "",
  action: "PROMOTE" as PromotionAction,
};

export function StudentsPage() {
  const { session, logout } = useAuth();
  const [students, setStudents] = useState<Paginated<StudentRecord>>(emptyPage);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [editingStudentId, setEditingStudentId] = useState<string | null>(null);
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState({
    yearId: "",
    classId: "",
    sectionId: "",
    status: "",
    q: "",
    includeInactive: false,
    page: 1,
  });
  const [studentForm, setStudentForm] = useState(emptyStudentForm);
  const [statusForm, setStatusForm] = useState<{ studentId: string; status: StudentStatus }>({
    studentId: "",
    status: "ACTIVE",
  });
  const [statusStudentSearch, setStatusStudentSearch] = useState("");
  const [promotionForm, setPromotionForm] = useState(emptyPromotionForm);

  const canManageStudents = session?.role === "SUPER_ADMIN" || session?.role === "ADMIN" || session?.role === "DATA_ENTRY";
  const canManageStatus = session?.role === "SUPER_ADMIN" || session?.role === "ADMIN";
  const canPromote = session?.role === "SUPER_ADMIN" || session?.role === "ADMIN";

  function buildStudentParams(page = filters.page) {
    const params = new URLSearchParams({
      page: String(page),
      size: "20",
      include_inactive: String(filters.includeInactive),
    });
    if (filters.yearId) {
      params.set("year_id", filters.yearId);
    }
    if (filters.classId) {
      params.set("class_id", filters.classId);
    }
    if (filters.sectionId) {
      params.set("section_id", filters.sectionId);
    }
    if (filters.status) {
      params.set("status", filters.status);
    }
    if (filters.q.trim()) {
      params.set("q", filters.q.trim());
    }
    return params;
  }

  useEffect(() => {
    if (!session) {
      return;
    }

    let isMounted = true;
    const token = session.accessToken;

    async function loadReferenceData() {
      try {
        const [years, classList, sectionList] = await Promise.all([
          apiRequest<AcademicYear[]>("/academic-years", { token }),
          apiRequest<ClassRoom[]>("/reference/classes", { token }),
          apiRequest<Section[]>("/reference/sections", { token }),
        ]);

        if (!isMounted) {
          return;
        }

        const activeYear = years.find((item) => item.is_active) || years[0];
        setAcademicYears(years);
        setClasses(classList);
        setSections(sectionList);
        setFilters((current) => ({
          ...current,
          yearId: current.yearId || activeYear?.id || "",
        }));
        setStudentForm((current) => ({
          ...current,
          academic_year_id: current.academic_year_id || activeYear?.id || "",
        }));
        setPromotionForm((current) => ({
          ...current,
          academic_year_from: current.academic_year_from || activeYear?.id || "",
          academic_year_to:
            current.academic_year_to || years.find((item) => item.id !== activeYear?.id)?.id || activeYear?.id || "",
        }));
      } catch (loadError) {
        if (isUnauthorizedError(loadError)) {
          logout();
          return;
        }
        if (isMounted) {
          setError(getErrorMessage(loadError));
        }
      }
    }

    loadReferenceData();

    return () => {
      isMounted = false;
    };
  }, [logout, session]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setFilters((current) => {
        if (current.q === searchInput) {
          return current;
        }
        return { ...current, q: searchInput, page: 1 };
      });
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  useEffect(() => {
    if (!session || !filters.yearId) {
      return;
    }

    let isMounted = true;
    const token = session.accessToken;

    async function loadStudents() {
      setLoading(true);
      setError("");

      try {
        const data = await apiRequest<Paginated<StudentRecord>>(`/students?${buildStudentParams().toString()}`, {
          token,
        });
        if (!isMounted) {
          return;
        }
        setStudents(data);
      } catch (loadError) {
        if (isUnauthorizedError(loadError)) {
          logout();
          return;
        }
        if (isMounted) {
          setError(getErrorMessage(loadError));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadStudents();

    return () => {
      isMounted = false;
    };
  }, [filters, logout, session]);

  const visibleSections = useMemo(
    () => sections.filter((section) => !studentForm.class_id || section.class_id === studentForm.class_id),
    [sections, studentForm.class_id],
  );
  const filteredSections = useMemo(
    () => sections.filter((section) => !filters.classId || section.class_id === filters.classId),
    [filters.classId, sections],
  );
  const visibleStudents = students.data;
  const statusStudentOptions = useMemo(
    () =>
      visibleStudents.filter((student) => {
        const term = statusStudentSearch.trim().toLowerCase();
        if (!term) {
          return true;
        }
        return `${student.first_name} ${student.last_name || ""} ${student.student_id || ""}`.toLowerCase().includes(term);
      }),
    [statusStudentSearch, visibleStudents],
  );
  const studentColumns = useMemo(
    () =>
      buildStudentColumns({
        canManageStudents,
        onEdit: startEditing,
        onToggleStudentSelection: toggleStudentSelection,
        selectedStudents,
      }),
    [canManageStudents, selectedStudents],
  );

  function resetStudentForm() {
    setEditingStudentId(null);
    setStudentForm((current) => ({
      ...emptyStudentForm,
      academic_year_id: current.academic_year_id || filters.yearId,
    }));
  }

  function startEditing(student: StudentRecord) {
    setEditingStudentId(student.id);
    setStudentForm({
      student_id: student.student_id || "",
      first_name: student.first_name,
      last_name: student.last_name || "",
      dob: student.dob,
      guardian_name: student.guardian_name || "",
      guardian_phone: student.guardian_phone || "",
      class_id: student.class_id || "",
      section_id: student.section_id || "",
      academic_year_id: student.academic_year_id || filters.yearId,
    });
  }

  function toggleStudentSelection(studentId: string) {
    setSelectedStudents((current) =>
      current.includes(studentId) ? current.filter((item) => item !== studentId) : [...current, studentId],
    );
  }

  async function handleStudentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    const payload = {
      student_id: studentForm.student_id || null,
      first_name: studentForm.first_name,
      last_name: studentForm.last_name || null,
      dob: studentForm.dob,
      guardian_name: studentForm.guardian_name || null,
      guardian_phone: studentForm.guardian_phone || null,
      class_id: studentForm.class_id,
      section_id: studentForm.section_id,
      academic_year_id: studentForm.academic_year_id,
    };

    try {
      const token = session.accessToken;
      if (editingStudentId) {
        await apiRequest(`/students/${editingStudentId}`, {
          method: "PUT",
          token,
          body: payload,
        });
        setMessage("Student updated successfully.");
      } else {
        await apiRequest("/students", {
          method: "POST",
          token,
          body: payload,
        });
        setMessage("Student created successfully.");
      }
      resetStudentForm();
      setFilters((current) => ({ ...current, page: 1 }));
      const refreshed = await apiRequest<Paginated<StudentRecord>>(`/students?${buildStudentParams(1).toString()}`, {
        token,
      });
      setStudents(refreshed);
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

  async function handleStatusSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !statusForm.studentId) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/students/${statusForm.studentId}/status`, {
        method: "PUT",
        token: session.accessToken,
        body: { status: statusForm.status },
      });
      setMessage("Student status updated.");
      setFilters((current) => ({ ...current }));
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

  async function handlePromotionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const result = await apiRequest<{ processed_count: number; action: PromotionAction; student_ids: string[] }>(
        "/students/promote",
        {
          method: "POST",
          token: session.accessToken,
          body: {
            academic_year_from: promotionForm.academic_year_from,
            academic_year_to: promotionForm.academic_year_to,
            student_ids: selectedStudents,
            action: promotionForm.action,
          },
        },
      );
      setMessage(`Promotion workflow completed for ${result.processed_count} student(s).`);
      setSelectedStudents([]);
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

  return (
    <>
      <PageIntro
        eyebrow="Admissions and roster"
        title="Students"
        description="Filter the roster by year, class, section, status, and student search. Authorized roles can create, update, transition, and promote records."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="split-grid">
        <StudentRosterPanel
          academicYears={academicYears}
          classes={classes}
          columns={studentColumns}
          filteredSections={filteredSections}
          filters={filters}
          loading={loading}
          searchInput={searchInput}
          students={students}
          onFiltersChange={setFilters}
          onSearchInputChange={setSearchInput}
        />
        <StudentMaintenancePanel
          academicYears={academicYears}
          canManageStatus={canManageStatus}
          canManageStudents={canManageStudents}
          classes={classes}
          editingStudentId={editingStudentId}
          onResetStudentForm={resetStudentForm}
          onSetStatusStudentSearch={setStatusStudentSearch}
          onStatusFormChange={setStatusForm}
          onStatusSubmit={handleStatusSubmit}
          onStudentFormChange={setStudentForm}
          onStudentSubmit={handleStudentSubmit}
          statusForm={statusForm}
          statusStudentOptions={statusStudentOptions}
          statusStudentSearch={statusStudentSearch}
          studentForm={studentForm}
          submitting={submitting}
          visibleSections={visibleSections}
        />
      </section>

      {canPromote ? (
        <StudentPromotionPanel
          academicYears={academicYears}
          onPromotionFormChange={setPromotionForm}
          onSubmit={handlePromotionSubmit}
          promotionForm={promotionForm}
          selectedStudents={selectedStudents}
          submitting={submitting}
        />
      ) : null}
    </>
  );
}
