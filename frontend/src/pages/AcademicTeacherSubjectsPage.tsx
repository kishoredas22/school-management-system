import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { Panel } from "../components/Panel";
import { AcademicWorkspace } from "../components/academics/AcademicWorkspace";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { AcademicYear, ClassRoom, Section, Subject, Teacher, TeacherSubjectAssignment } from "../types";

const emptyForm = {
  teacher_id: "",
  subject_id: "",
  academic_year_id: "",
  class_id: "",
  section_id: "",
};

export function AcademicTeacherSubjectsPage() {
  const { session, logout } = useAuth();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mappings, setMappings] = useState<TeacherSubjectAssignment[]>([]);
  const [yearFilter, setYearFilter] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const visibleSections = useMemo(
    () => sections.filter((section) => !form.class_id || section.class_id === form.class_id),
    [form.class_id, sections],
  );

  async function loadReferences() {
    if (!session) {
      return;
    }

    try {
      const [years, classList, sectionList, teacherList, subjectList] = await Promise.all([
        apiRequest<AcademicYear[]>("/academic-years", { token: session.accessToken }),
        apiRequest<ClassRoom[]>("/reference/classes", { token: session.accessToken }),
        apiRequest<Section[]>("/reference/sections", { token: session.accessToken }),
        apiRequest<Teacher[]>("/teachers", { token: session.accessToken }),
        apiRequest<Subject[]>("/academics/subjects", { token: session.accessToken }),
      ]);
      const activeYear = years.find((item) => item.is_active) || years[0];
      setAcademicYears(years);
      setClasses(classList);
      setSections(sectionList);
      setTeachers(teacherList);
      setSubjects(subjectList.filter((item) => item.is_active));
      setYearFilter((current) => current || activeYear?.id || "");
      setForm((current) => ({ ...current, academic_year_id: current.academic_year_id || activeYear?.id || "" }));
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

  async function loadMappings() {
    if (!session) {
      return;
    }

    try {
      const params = new URLSearchParams();
      if (yearFilter) {
        params.set("year_id", yearFilter);
      }
      if (classFilter) {
        params.set("class_id", classFilter);
      }
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const data = await apiRequest<TeacherSubjectAssignment[]>(`/academics/teacher-subjects${suffix}`, {
        token: session.accessToken,
      });
      setMappings(data);
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    }
  }

  useEffect(() => {
    loadReferences();
  }, [session]);

  useEffect(() => {
    if (!session) {
      return;
    }
    loadMappings();
  }, [session, yearFilter, classFilter]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest<TeacherSubjectAssignment>("/academics/teacher-subjects", {
        method: "POST",
        token: session.accessToken,
        body: {
          teacher_id: form.teacher_id,
          subject_id: form.subject_id,
          academic_year_id: form.academic_year_id,
          class_id: form.class_id,
          section_id: form.section_id || null,
        },
      });
      setMessage("Teacher-subject mapping created.");
      setForm((current) => ({ ...emptyForm, academic_year_id: current.academic_year_id }));
      await loadMappings();
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
    <AcademicWorkspace
      title="Teacher-Subject Mapping"
      description="Map each teacher to the subject, academic year, and class/section scope that powers marks-entry access."
    >
      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="split-grid">
        <Panel title="Mappings" subtitle="Review the current teacher-subject scopes used for marks-entry authorization.">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="mapping-filter-year">Academic year</label>
              <select id="mapping-filter-year" value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
                <option value="">All academic years</option>
                {academicYears.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="mapping-filter-class">Class</label>
              <select id="mapping-filter-class" value={classFilter} onChange={(event) => setClassFilter(event.target.value)}>
                <option value="">All classes</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <DataTable<TeacherSubjectAssignment>
            rows={mappings}
            emptyMessage={loading ? "Loading mappings..." : "No teacher-subject mappings created yet."}
            columns={[
              {
                key: "teacher",
                label: "Teacher",
                render: (row) => (
                  <div className="field-stack">
                    <strong>{row.teacher_name}</strong>
                    <span className="panel-note">{row.subject_name}</span>
                  </div>
                ),
              },
              { key: "year", label: "Year", render: (row) => row.academic_year_name },
              {
                key: "scope",
                label: "Scope",
                render: (row) => `${row.class_name}${row.section_name ? ` / ${row.section_name}` : " / Whole class"}`,
              },
            ]}
          />
        </Panel>

        <Panel title="Create mapping" subtitle="This scope is combined with the teacher profile assignment before marks access is granted.">
          <form className="field-stack" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="mapping-year">Academic year</label>
                <select
                  id="mapping-year"
                  value={form.academic_year_id}
                  onChange={(event) => setForm((current) => ({ ...current, academic_year_id: event.target.value }))}
                  required
                >
                  <option value="">Select academic year</option>
                  {academicYears.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="mapping-class">Class</label>
                <select
                  id="mapping-class"
                  value={form.class_id}
                  onChange={(event) =>
                    setForm((current) => ({
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
                <label htmlFor="mapping-section">Section</label>
                <select
                  id="mapping-section"
                  value={form.section_id}
                  onChange={(event) => setForm((current) => ({ ...current, section_id: event.target.value }))}
                >
                  <option value="">Whole class</option>
                  {visibleSections.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="mapping-teacher">Teacher</label>
                <select
                  id="mapping-teacher"
                  value={form.teacher_id}
                  onChange={(event) => setForm((current) => ({ ...current, teacher_id: event.target.value }))}
                  required
                >
                  <option value="">Select teacher</option>
                  {teachers.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field field-span-2">
                <label htmlFor="mapping-subject">Subject</label>
                <select
                  id="mapping-subject"
                  value={form.subject_id}
                  onChange={(event) => setForm((current) => ({ ...current, subject_id: event.target.value }))}
                  required
                >
                  <option value="">Select subject</option>
                  {subjects.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} ({item.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Saving..." : "Create mapping"}
              </button>
            </div>
          </form>
        </Panel>
      </section>
    </AcademicWorkspace>
  );
}
