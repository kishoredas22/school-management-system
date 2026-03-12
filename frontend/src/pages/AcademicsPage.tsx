import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { MetricCard } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatDate } from "../lib/format";
import type { AcademicYear, ClassRoom, Exam, ExamStatus, Section, Subject } from "../types";

interface ExamSubjectDraft {
  subject_id: string;
  max_marks: string;
  pass_marks: string;
}

const defaultSubjectDraft = (): ExamSubjectDraft => ({
  subject_id: "",
  max_marks: "100",
  pass_marks: "35",
});

const emptyExamForm = {
  academic_year_id: "",
  class_id: "",
  section_id: "",
  name: "",
  term_label: "",
  start_date: "",
  end_date: "",
  subjects: [defaultSubjectDraft()],
};

export function AcademicsPage() {
  const { session, logout } = useAuth();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [yearFilter, setYearFilter] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [examForm, setExamForm] = useState(emptyExamForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [statusUpdatingId, setStatusUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const availableSections = useMemo(
    () => sections.filter((section) => !examForm.class_id || section.class_id === examForm.class_id),
    [examForm.class_id, sections],
  );
  const activeSubjects = useMemo(() => subjects.filter((subject) => subject.is_active), [subjects]);

  async function loadReferences() {
    if (!session) {
      return;
    }

    setError("");

    try {
      const [yearList, classList, sectionList, subjectList] = await Promise.all([
        apiRequest<AcademicYear[]>("/academic-years", { token: session.accessToken }),
        apiRequest<ClassRoom[]>("/reference/classes", { token: session.accessToken }),
        apiRequest<Section[]>("/reference/sections", { token: session.accessToken }),
        apiRequest<Subject[]>("/academics/subjects", { token: session.accessToken }),
      ]);

      const activeYear = yearList.find((item) => item.is_active) || yearList[0];
      setAcademicYears(yearList);
      setClasses(classList);
      setSections(sectionList);
      setSubjects(subjectList);
      setYearFilter((current) => current || activeYear?.id || "");
      setExamForm((current) => ({
        ...current,
        academic_year_id: current.academic_year_id || activeYear?.id || "",
      }));
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    }
  }

  async function loadExams() {
    if (!session) {
      return;
    }

    setError("");

    try {
      const query = new URLSearchParams();
      if (yearFilter) {
        query.set("year_id", yearFilter);
      }
      if (classFilter) {
        query.set("class_id", classFilter);
      }
      const suffix = query.toString() ? `?${query.toString()}` : "";
      const examList = await apiRequest<Exam[]>(`/academics/exams${suffix}`, {
        token: session.accessToken,
      });
      setExams(examList);
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    }
  }

  useEffect(() => {
    if (!session) {
      return;
    }

    let isMounted = true;

    async function initialize() {
      setLoading(true);
      await loadReferences();
      if (isMounted) {
        setLoading(false);
      }
    }

    initialize();

    return () => {
      isMounted = false;
    };
  }, [session]);

  useEffect(() => {
    if (!session) {
      return;
    }

    loadExams();
  }, [session, yearFilter, classFilter]);

  function updateSubjectDraft(index: number, field: keyof ExamSubjectDraft, value: string) {
    setExamForm((current) => ({
      ...current,
      subjects: current.subjects.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)),
    }));
  }

  function addSubjectDraft() {
    setExamForm((current) => ({
      ...current,
      subjects: [...current.subjects, defaultSubjectDraft()],
    }));
  }

  function removeSubjectDraft(index: number) {
    setExamForm((current) => ({
      ...current,
      subjects: current.subjects.length === 1 ? current.subjects : current.subjects.filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  function resetForm() {
    setExamForm((current) => ({
      ...emptyExamForm,
      academic_year_id: current.academic_year_id,
    }));
  }

  function validateForm() {
    if (!examForm.academic_year_id || !examForm.class_id || !examForm.name || !examForm.start_date || !examForm.end_date) {
      return "Fill the exam name, academic year, class, and date range before saving.";
    }

    if (!examForm.subjects.length) {
      return "Add at least one subject to the exam setup.";
    }

    const selectedSubjectIds = examForm.subjects.map((item) => item.subject_id).filter(Boolean);
    if (selectedSubjectIds.length !== examForm.subjects.length) {
      return "Each subject row must have a subject selected.";
    }

    if (new Set(selectedSubjectIds).size !== selectedSubjectIds.length) {
      return "Each subject can only be added once in an exam.";
    }

    for (const item of examForm.subjects) {
      const maxMarks = Number(item.max_marks);
      const passMarks = Number(item.pass_marks);
      if (!Number.isFinite(maxMarks) || !Number.isFinite(passMarks) || maxMarks <= 0 || passMarks < 0) {
        return "Enter valid max marks and pass marks for every subject.";
      }
      if (passMarks > maxMarks) {
        return "Pass marks cannot be greater than max marks.";
      }
    }

    return "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    const validationMessage = validateForm();
    if (validationMessage) {
      setError(validationMessage);
      setMessage("");
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest<Exam>("/academics/exams", {
        method: "POST",
        token: session.accessToken,
        body: {
          academic_year_id: examForm.academic_year_id,
          class_id: examForm.class_id,
          section_id: examForm.section_id || null,
          name: examForm.name,
          term_label: examForm.term_label || null,
          start_date: examForm.start_date,
          end_date: examForm.end_date,
          subjects: examForm.subjects.map((item) => ({
            subject_id: item.subject_id,
            max_marks: item.max_marks,
            pass_marks: item.pass_marks,
          })),
        },
      });
      setMessage("Exam setup created successfully.");
      resetForm();
      await loadExams();
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

  async function handleStatusChange(examId: string, status: ExamStatus) {
    if (!session) {
      return;
    }

    setStatusUpdatingId(examId);
    setError("");
    setMessage("");

    try {
      await apiRequest<Exam>(`/academics/exams/${examId}/status`, {
        method: "PUT",
        token: session.accessToken,
        body: { status },
      });
      setMessage(status === "PUBLISHED" ? "Exam published successfully." : "Exam moved back to draft.");
      await loadExams();
    } catch (statusError) {
      if (isUnauthorizedError(statusError)) {
        logout();
        return;
      }
      setError(getErrorMessage(statusError));
    } finally {
      setStatusUpdatingId(null);
    }
  }

  const publishedCount = exams.filter((item) => item.status === "PUBLISHED").length;
  const draftCount = exams.filter((item) => item.status === "DRAFT").length;

  return (
    <>
      <PageIntro
        eyebrow="Academic management"
        title="Academics"
        description="Set up exam cycles with academic year, class, section, dates, and subject-wise mark rules. This is the first academic layer for later marks entry, report cards, and promotions."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="metric-grid">
        <MetricCard label="Exam cycles" value={String(exams.length)} detail="Configured exams in the selected view" tone="sand" />
        <MetricCard label="Draft" value={String(draftCount)} detail="Still open for setup or revision" tone="mint" />
        <MetricCard label="Published" value={String(publishedCount)} detail="Ready for academic reporting" tone="ink" />
        <MetricCard
          label="Active subjects"
          value={String(activeSubjects.length)}
          detail="Available subject master entries for exam setup"
          tone="coral"
        />
      </section>

      <section className="split-grid">
        <Panel title="Exam register" subtitle="Filter the academic exam calendar by year and class, then publish or reopen any exam.">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="exam-filter-year">Academic year</label>
              <select id="exam-filter-year" value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
                <option value="">All academic years</option>
                {academicYears.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="exam-filter-class">Class</label>
              <select id="exam-filter-class" value={classFilter} onChange={(event) => setClassFilter(event.target.value)}>
                <option value="">All classes</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <DataTable<Exam>
            columns={[
              {
                key: "name",
                label: "Exam",
                render: (row) => (
                  <div className="field-stack">
                    <strong>{row.name}</strong>
                    <span className="panel-note">{row.term_label || "No term label"}</span>
                  </div>
                ),
              },
              {
                key: "scope",
                label: "Scope",
                render: (row) => (
                  <div className="field-stack">
                    <span>
                      {row.academic_year_name} · {row.class_name}
                      {row.section_name ? ` · ${row.section_name}` : ""}
                    </span>
                    <span className="panel-note">
                      {formatDate(row.start_date)} to {formatDate(row.end_date)}
                    </span>
                  </div>
                ),
              },
              {
                key: "subjects",
                label: "Subjects",
                render: (row) => (
                  <div className="badge-stack">
                    {row.subjects.map((subject) => (
                      <span key={subject.id} className="chip">
                        {subject.subject_name} · {subject.pass_marks}/{subject.max_marks}
                      </span>
                    ))}
                  </div>
                ),
              },
              {
                key: "status",
                label: "Status",
                render: (row) => (
                  <span
                    className={`status-pill ${row.status === "PUBLISHED" ? "status-published" : "status-draft"}`.trim()}
                  >
                    {row.status}
                  </span>
                ),
              },
              {
                key: "actions",
                label: "Actions",
                render: (row) => (
                  <div className="inline-actions">
                    {row.status === "DRAFT" ? (
                      <button
                        className="primary-button"
                        type="button"
                        disabled={statusUpdatingId === row.id}
                        onClick={() => handleStatusChange(row.id, "PUBLISHED")}
                      >
                        Publish
                      </button>
                    ) : (
                      <button
                        className="ghost-button"
                        type="button"
                        disabled={statusUpdatingId === row.id}
                        onClick={() => handleStatusChange(row.id, "DRAFT")}
                      >
                        Move to draft
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
            rows={exams}
            emptyMessage={loading ? "Loading exams..." : "No exams match the current academic filters."}
          />
        </Panel>

        <Panel title="Create exam" subtitle="Build a new exam with its subject-wise max marks and pass marks in one place.">
          {!activeSubjects.length ? (
            <div className="message-banner">
              No active subjects are available yet. Exam setup becomes fully usable once subject master entries are added.
            </div>
          ) : null}

          <form className="field-stack" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="exam-form-year">Academic year</label>
                <select
                  id="exam-form-year"
                  value={examForm.academic_year_id}
                  onChange={(event) => setExamForm((current) => ({ ...current, academic_year_id: event.target.value }))}
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
                <label htmlFor="exam-form-class">Class</label>
                <select
                  id="exam-form-class"
                  value={examForm.class_id}
                  onChange={(event) =>
                    setExamForm((current) => ({
                      ...current,
                      class_id: event.target.value,
                      section_id:
                        current.section_id && sections.some((item) => item.id === current.section_id && item.class_id === event.target.value)
                          ? current.section_id
                          : "",
                    }))
                  }
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
                <label htmlFor="exam-form-section">Section</label>
                <select
                  id="exam-form-section"
                  value={examForm.section_id}
                  onChange={(event) => setExamForm((current) => ({ ...current, section_id: event.target.value }))}
                >
                  <option value="">Whole class</option>
                  {availableSections.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="exam-form-term">Term label</label>
                <input
                  id="exam-form-term"
                  type="text"
                  value={examForm.term_label}
                  onChange={(event) => setExamForm((current) => ({ ...current, term_label: event.target.value }))}
                  placeholder="Term 1 / Half Yearly"
                />
              </div>

              <div className="field field-span-2">
                <label htmlFor="exam-form-name">Exam name</label>
                <input
                  id="exam-form-name"
                  type="text"
                  value={examForm.name}
                  onChange={(event) => setExamForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Quarterly Assessment"
                />
              </div>

              <div className="field">
                <label htmlFor="exam-form-start">Start date</label>
                <input
                  id="exam-form-start"
                  type="date"
                  value={examForm.start_date}
                  onChange={(event) => setExamForm((current) => ({ ...current, start_date: event.target.value }))}
                />
              </div>

              <div className="field">
                <label htmlFor="exam-form-end">End date</label>
                <input
                  id="exam-form-end"
                  type="date"
                  value={examForm.end_date}
                  onChange={(event) => setExamForm((current) => ({ ...current, end_date: event.target.value }))}
                />
              </div>
            </div>

            <div className="field-stack">
              <div className="panel-head">
                <div>
                  <h2>Subject blueprint</h2>
                  <p>Choose the included subjects and define max marks and pass marks for each one.</p>
                </div>
                <button className="ghost-button" type="button" onClick={addSubjectDraft}>
                  Add subject
                </button>
              </div>

              {examForm.subjects.map((item, index) => (
                <div key={`subject-row-${index}`} className="academic-subject-row">
                  <div className="field">
                    <label htmlFor={`exam-subject-${index}`}>Subject</label>
                    <select
                      id={`exam-subject-${index}`}
                      value={item.subject_id}
                      onChange={(event) => updateSubjectDraft(index, "subject_id", event.target.value)}
                    >
                      <option value="">Select subject</option>
                      {activeSubjects.map((subject) => (
                        <option key={subject.id} value={subject.id}>
                          {subject.name} ({subject.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="field">
                    <label htmlFor={`exam-max-${index}`}>Max marks</label>
                    <input
                      id={`exam-max-${index}`}
                      type="number"
                      min="1"
                      step="0.01"
                      value={item.max_marks}
                      onChange={(event) => updateSubjectDraft(index, "max_marks", event.target.value)}
                    />
                  </div>

                  <div className="field">
                    <label htmlFor={`exam-pass-${index}`}>Pass marks</label>
                    <input
                      id={`exam-pass-${index}`}
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.pass_marks}
                      onChange={(event) => updateSubjectDraft(index, "pass_marks", event.target.value)}
                    />
                  </div>

                  <div className="field academic-row-action">
                    <label>&nbsp;</label>
                    <button
                      className="soft-button"
                      type="button"
                      disabled={examForm.subjects.length === 1}
                      onClick={() => removeSubjectDraft(index)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting || !activeSubjects.length}>
                {submitting ? "Saving exam..." : "Create exam"}
              </button>
              <button className="ghost-button" type="button" onClick={resetForm}>
                Reset
              </button>
            </div>
          </form>
        </Panel>
      </section>
    </>
  );
}
