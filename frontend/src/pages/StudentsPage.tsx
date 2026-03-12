import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatDate, fullName } from "../lib/format";
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

    async function loadReferenceData() {
      try {
        const [years, classList, sectionList] = await Promise.all([
          apiRequest<AcademicYear[]>("/academic-years", { token: session!.accessToken }),
          apiRequest<ClassRoom[]>("/reference/classes", { token: session!.accessToken }),
          apiRequest<Section[]>("/reference/sections", { token: session!.accessToken }),
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
    if (!session || !filters.yearId) {
      return;
    }

    let isMounted = true;

    async function loadStudents() {
      setLoading(true);
      setError("");

      try {
        const data = await apiRequest<Paginated<StudentRecord>>(`/students?${buildStudentParams().toString()}`, {
          token: session!.accessToken,
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

  const visibleSections = sections.filter(
    (section) => !studentForm.class_id || section.class_id === studentForm.class_id,
  );

  const filteredSections = sections.filter((section) => !filters.classId || section.class_id === filters.classId);
  const visibleStudents = students.data;
  const statusStudentOptions = visibleStudents.filter((student) => {
    const term = statusStudentSearch.trim().toLowerCase();
    if (!term) {
      return true;
    }
    return `${student.first_name} ${student.last_name || ""} ${student.student_id || ""}`.toLowerCase().includes(term);
  });

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
      if (editingStudentId) {
        await apiRequest(`/students/${editingStudentId}`, {
          method: "PUT",
          token: session!.accessToken,
          body: payload,
        });
        setMessage("Student updated successfully.");
      } else {
        await apiRequest("/students", {
          method: "POST",
          token: session!.accessToken,
          body: payload,
        });
        setMessage("Student created successfully.");
      }
      resetStudentForm();
      setFilters((current) => ({ ...current, page: 1 }));
      const refreshed = await apiRequest<Paginated<StudentRecord>>(`/students?${buildStudentParams(1).toString()}`, {
        token: session!.accessToken,
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
        token: session!.accessToken,
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
          token: session!.accessToken,
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
        <Panel title="Roster browser" subtitle="Live backend list with year, class, section, status, and student search filters.">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="filter-year">Academic year</label>
              <select
                id="filter-year"
                value={filters.yearId}
                onChange={(event) => setFilters((current) => ({ ...current, yearId: event.target.value, page: 1 }))}
              >
                <option value="">Select year</option>
                {academicYears.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="filter-class">Class</label>
              <select
                id="filter-class"
                value={filters.classId}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    classId: event.target.value,
                    sectionId: "",
                    page: 1,
                  }))
                }
              >
                <option value="">All classes</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="filter-section">Section</label>
              <select
                id="filter-section"
                value={filters.sectionId}
                onChange={(event) => setFilters((current) => ({ ...current, sectionId: event.target.value }))}
              >
                <option value="">All sections</option>
                {filteredSections.map((section) => (
                  <option key={section.id} value={section.id}>
                    {section.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="filter-status">Status</label>
              <select
                id="filter-status"
                value={filters.status}
                onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value, page: 1 }))}
              >
                <option value="">All statuses</option>
                {["ACTIVE", "PASSED_OUT", "TOOK_TC", "INACTIVE"].map((status) => (
                  <option key={status} value={status}>
                    {status.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>

            <div className="field field-span-2">
              <label htmlFor="filter-search">Search student</label>
              <input
                id="filter-search"
                value={filters.q}
                onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value, page: 1 }))}
                placeholder="Search by student name or code"
              />
            </div>
          </div>

          <div className="toolbar">
            <label className="check-item">
              <input
                type="checkbox"
                checked={filters.includeInactive}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    includeInactive: event.target.checked,
                    page: 1,
                  }))
                }
              />
              Include inactive students
            </label>
            <span className="field-note">
              {loading ? "Loading..." : `${students.total_records} total records | ${visibleStudents.length} shown on this page`}
            </span>
          </div>

          <DataTable
            rows={visibleStudents}
            emptyMessage="No students match the current filter."
            columns={[
              {
                key: "select",
                label: "",
                render: (row) => (
                  <input
                    type="checkbox"
                    checked={selectedStudents.includes(row.id)}
                    onChange={() => toggleStudentSelection(row.id)}
                  />
                ),
              },
              {
                key: "student",
                label: "Student",
                render: (row) => (
                  <div>
                    <strong>{fullName(row.first_name, row.last_name)}</strong>
                    <div className="field-note">{row.student_id || "Student ID pending"}</div>
                  </div>
                ),
              },
              {
                key: "class",
                label: "Placement",
                render: (row) => (
                  <div>
                    <strong>{row.class_name || "No class"}</strong>
                    <div className="field-note">{row.section_name || "No section"}</div>
                  </div>
                ),
              },
              {
                key: "guardian",
                label: "Guardian",
                render: (row) => (
                  <div>
                    <strong>{row.guardian_name || "Not set"}</strong>
                    <div className="field-note">{row.guardian_phone || "No phone"}</div>
                  </div>
                ),
              },
              {
                key: "dob",
                label: "DOB",
                render: (row) => formatDate(row.dob),
              },
              {
                key: "status",
                label: "Status",
                render: (row) => (
                  <div className={`status-pill status-${row.status.toLowerCase().replace("_", "")}`}>
                    {row.status.replace(/_/g, " ")}
                  </div>
                ),
              },
              {
                key: "actions",
                label: "Actions",
                render: (row) =>
                  canManageStudents ? (
                    <button className="ghost-button" type="button" onClick={() => startEditing(row)}>
                      Edit
                    </button>
                  ) : (
                    <span className="field-note">Read only</span>
                  ),
              },
            ]}
          />

          <div className="toolbar">
            <button
              className="ghost-button"
              type="button"
              disabled={filters.page <= 1}
              onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}
            >
              Previous
            </button>
            <span className="field-note">
              Page {students.page} of {Math.max(students.total_pages, 1)}
            </span>
            <button
              className="ghost-button"
              type="button"
              disabled={students.page >= Math.max(students.total_pages, 1)}
              onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}
            >
              Next
            </button>
          </div>
        </Panel>

        <Panel
          title={editingStudentId ? "Edit student" : "Register student"}
          subtitle={canManageStudents ? "Create or revise a student master record." : "Your role can review records only."}
        >
          {canManageStudents ? (
            <form className="field-stack" onSubmit={handleStudentSubmit}>
              <div className="form-grid">
                <div className="field">
                  <label htmlFor="student-id">Student code</label>
                  <input
                    id="student-id"
                    value={studentForm.student_id}
                    onChange={(event) => setStudentForm((current) => ({ ...current, student_id: event.target.value }))}
                    placeholder="Leave blank for auto-generation"
                  />
                </div>
                <div className="field">
                  <label htmlFor="dob">Date of birth</label>
                  <input
                    id="dob"
                    type="date"
                    value={studentForm.dob}
                    onChange={(event) => setStudentForm((current) => ({ ...current, dob: event.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="first-name">First name</label>
                  <input
                    id="first-name"
                    value={studentForm.first_name}
                    onChange={(event) => setStudentForm((current) => ({ ...current, first_name: event.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="last-name">Last name</label>
                  <input
                    id="last-name"
                    value={studentForm.last_name}
                    onChange={(event) => setStudentForm((current) => ({ ...current, last_name: event.target.value }))}
                  />
                </div>
                <div className="field">
                  <label htmlFor="guardian-name">Guardian name</label>
                  <input
                    id="guardian-name"
                    value={studentForm.guardian_name}
                    onChange={(event) =>
                      setStudentForm((current) => ({ ...current, guardian_name: event.target.value }))
                    }
                  />
                </div>
                <div className="field">
                  <label htmlFor="guardian-phone">Guardian phone</label>
                  <input
                    id="guardian-phone"
                    value={studentForm.guardian_phone}
                    onChange={(event) =>
                      setStudentForm((current) => ({ ...current, guardian_phone: event.target.value }))
                    }
                  />
                </div>
                <div className="field">
                  <label htmlFor="student-year">Academic year</label>
                  <select
                    id="student-year"
                    value={studentForm.academic_year_id}
                    onChange={(event) =>
                      setStudentForm((current) => ({ ...current, academic_year_id: event.target.value }))
                    }
                    required
                  >
                    <option value="">Select year</option>
                    {academicYears.map((year) => (
                      <option key={year.id} value={year.id}>
                        {year.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="student-class">Class</label>
                  <select
                    id="student-class"
                    value={studentForm.class_id}
                    onChange={(event) =>
                      setStudentForm((current) => ({
                        ...current,
                        class_id: event.target.value,
                        section_id: "",
                      }))
                    }
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
                  <label htmlFor="student-section">Section</label>
                  <select
                    id="student-section"
                    value={studentForm.section_id}
                    onChange={(event) => setStudentForm((current) => ({ ...current, section_id: event.target.value }))}
                    required
                  >
                    <option value="">Select section</option>
                    {visibleSections.map((section) => (
                      <option key={section.id} value={section.id}>
                        {section.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-actions">
                <button className="accent-button" type="submit" disabled={submitting}>
                  {submitting ? "Saving..." : editingStudentId ? "Update student" : "Create student"}
                </button>
                <button className="ghost-button" type="button" onClick={resetStudentForm}>
                  Clear
                </button>
              </div>
            </form>
          ) : (
            <div className="empty-state">Teachers can review the roster here, but student record changes remain disabled.</div>
          )}

          {canManageStatus ? (
            <form className="field-stack" onSubmit={handleStatusSubmit}>
              <div className="panel-head">
                <div>
                  <h2>Student status</h2>
                  <p>Administrative status transitions are handled separately from the edit form.</p>
                </div>
              </div>
              <div className="form-grid">
                <div className="field field-span-2">
                  <label htmlFor="status-search">Search student</label>
                  <input
                    id="status-search"
                    value={statusStudentSearch}
                    onChange={(event) => setStatusStudentSearch(event.target.value)}
                    placeholder="Search by student name or code"
                  />
                </div>
                <div className="field">
                  <label htmlFor="status-student">Student</label>
                  <select
                    id="status-student"
                    value={statusForm.studentId}
                    onChange={(event) => setStatusForm((current) => ({ ...current, studentId: event.target.value }))}
                  >
                    <option value="">Select student</option>
                    {statusStudentOptions.map((student) => (
                      <option key={student.id} value={student.id}>
                        {fullName(student.first_name, student.last_name)} ({student.student_id || "Pending ID"})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="status-value">Status</label>
                  <select
                    id="status-value"
                    value={statusForm.status}
                    onChange={(event) =>
                      setStatusForm((current) => ({ ...current, status: event.target.value as StudentStatus }))
                    }
                  >
                    {["ACTIVE", "PASSED_OUT", "TOOK_TC", "INACTIVE"].map((status) => (
                      <option key={status} value={status}>
                        {status.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-actions">
                <button className="soft-button" type="submit" disabled={submitting}>
                  Apply status
                </button>
              </div>
            </form>
          ) : null}
        </Panel>
      </section>

      {canPromote ? (
        <Panel title="Promotion workflow" subtitle="Apply year transition rules to selected students or the supplied year pair.">
          <form className="field-stack" onSubmit={handlePromotionSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="promote-from">From year</label>
                <select
                  id="promote-from"
                  value={promotionForm.academic_year_from}
                  onChange={(event) =>
                    setPromotionForm((current) => ({ ...current, academic_year_from: event.target.value }))
                  }
                >
                  <option value="">Select year</option>
                  {academicYears.map((year) => (
                    <option key={year.id} value={year.id}>
                      {year.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="promote-to">To year</label>
                <select
                  id="promote-to"
                  value={promotionForm.academic_year_to}
                  onChange={(event) =>
                    setPromotionForm((current) => ({ ...current, academic_year_to: event.target.value }))
                  }
                >
                  <option value="">Select year</option>
                  {academicYears.map((year) => (
                    <option key={year.id} value={year.id}>
                      {year.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="promotion-action">Action</label>
                <select
                  id="promotion-action"
                  value={promotionForm.action}
                  onChange={(event) =>
                    setPromotionForm((current) => ({
                      ...current,
                      action: event.target.value as PromotionAction,
                    }))
                  }
                >
                  {["PROMOTE", "HOLD", "PASS_OUT"].map((action) => (
                    <option key={action} value={action}>
                      {action.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="toolbar">
              <span className="field-note">{selectedStudents.length} student(s) selected on the current page.</span>
              <button className="accent-button" type="submit" disabled={submitting}>
                Run workflow
              </button>
            </div>
          </form>
        </Panel>
      ) : null}
    </>
  );
}
