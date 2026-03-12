import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { DataTable } from "../components/DataTable";
import { Panel } from "../components/Panel";
import { AcademicWorkspace } from "../components/academics/AcademicWorkspace";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { AcademicYear, ClassRoom, Exam, MarkRegisterRow } from "../types";

interface MarkDraft {
  marks_obtained: string;
  is_absent: boolean;
  remark: string;
}

export function AcademicMarksPage() {
  const { session, logout } = useAuth();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedYearId, setSelectedYearId] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");
  const [selectedExamId, setSelectedExamId] = useState("");
  const [selectedExamSubjectId, setSelectedExamSubjectId] = useState("");
  const [search, setSearch] = useState("");
  const [registerRows, setRegisterRows] = useState<MarkRegisterRow[]>([]);
  const [drafts, setDrafts] = useState<Record<string, MarkDraft>>({});
  const [loading, setLoading] = useState(true);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedExam = exams.find((exam) => exam.id === selectedExamId) || null;
  const selectedSubject = selectedExam?.subjects.find((item) => item.id === selectedExamSubjectId) || null;

  async function loadReferences() {
    if (!session) {
      return;
    }

    try {
      const [years, classList] = await Promise.all([
        apiRequest<AcademicYear[]>("/academic-years", { token: session.accessToken }),
        apiRequest<ClassRoom[]>("/reference/classes", { token: session.accessToken }),
      ]);
      const activeYear = years.find((item) => item.is_active) || years[0];
      setAcademicYears(years);
      setClasses(classList);
      setSelectedYearId((current) => current || activeYear?.id || "");
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

  async function loadExams() {
    if (!session) {
      return;
    }

    try {
      const params = new URLSearchParams();
      if (selectedYearId) {
        params.set("year_id", selectedYearId);
      }
      if (selectedClassId) {
        params.set("class_id", selectedClassId);
      }
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const data = await apiRequest<Exam[]>(`/academics/exams${suffix}`, { token: session.accessToken });
      setExams(data);
      setSelectedExamId((current) => (data.some((item) => item.id === current) ? current : data[0]?.id || ""));
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    }
  }

  async function loadRegister() {
    if (!session || !selectedExamSubjectId) {
      setRegisterRows([]);
      setDrafts({});
      return;
    }

    setRegisterLoading(true);
    try {
      const suffix = search.trim() ? `?q=${encodeURIComponent(search.trim())}` : "";
      const data = await apiRequest<MarkRegisterRow[]>(
        `/academics/exam-subjects/${selectedExamSubjectId}/marks${suffix}`,
        { token: session.accessToken },
      );
      setRegisterRows(data);
      setDrafts(
        Object.fromEntries(
          data.map((row) => [
            row.student_id,
            {
              marks_obtained: row.marks_obtained ?? "",
              is_absent: row.is_absent,
              remark: row.remark ?? "",
            },
          ]),
        ),
      );
    } catch (loadError) {
      if (isUnauthorizedError(loadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(loadError));
    } finally {
      setRegisterLoading(false);
    }
  }

  useEffect(() => {
    loadReferences();
  }, [session]);

  useEffect(() => {
    if (!session) {
      return;
    }
    loadExams();
  }, [session, selectedYearId, selectedClassId]);

  useEffect(() => {
    const nextSubjectId =
      selectedExam?.subjects.find((item) => item.id === selectedExamSubjectId)?.id || selectedExam?.subjects[0]?.id || "";
    setSelectedExamSubjectId(nextSubjectId);
  }, [selectedExamId, exams]);

  useEffect(() => {
    if (!session || !selectedExamSubjectId) {
      return;
    }
    loadRegister();
  }, [session, selectedExamSubjectId]);

  function updateDraft(studentId: string, next: Partial<MarkDraft>) {
    setDrafts((current) => ({
      ...current,
      [studentId]: {
        ...current[studentId],
        ...next,
      },
    }));
  }

  async function handleSave() {
    if (!session || !selectedExamSubjectId) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest<{ processed_count: number }>(`/academics/exam-subjects/${selectedExamSubjectId}/marks`, {
        method: "POST",
        token: session.accessToken,
        body: {
          entries: registerRows.map((row) => ({
            student_id: row.student_id,
            marks_obtained: drafts[row.student_id]?.is_absent
              ? null
              : drafts[row.student_id]?.marks_obtained === ""
                ? null
                : Number(drafts[row.student_id]?.marks_obtained),
            is_absent: Boolean(drafts[row.student_id]?.is_absent),
            remark: drafts[row.student_id]?.remark?.trim() || null,
          })),
        },
      });
      setMessage("Marks register saved.");
      await loadRegister();
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
      title="Marks Register"
      description="Open a scoped exam subject register, record subject-wise marks student by student, and capture absent flags and remarks from the same page."
    >
      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="split-grid">
        <Panel title="Register scope" subtitle="Choose the exam and subject you want to evaluate. Teacher accounts only see the scopes assigned to them.">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="marks-year">Academic year</label>
              <select id="marks-year" value={selectedYearId} onChange={(event) => setSelectedYearId(event.target.value)}>
                <option value="">All academic years</option>
                {academicYears.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="marks-class">Class</label>
              <select id="marks-class" value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}>
                <option value="">All classes</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field field-span-2">
              <label htmlFor="marks-exam">Exam</label>
              <select id="marks-exam" value={selectedExamId} onChange={(event) => setSelectedExamId(event.target.value)}>
                <option value="">Select exam</option>
                {exams.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} | {item.class_name}
                    {item.section_name ? ` / ${item.section_name}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="field field-span-2">
              <label htmlFor="marks-subject">Subject</label>
              <select
                id="marks-subject"
                value={selectedExamSubjectId}
                onChange={(event) => setSelectedExamSubjectId(event.target.value)}
                disabled={!selectedExam}
              >
                <option value="">Select subject</option>
                {selectedExam?.subjects.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.subject_name} | Pass {item.pass_marks} / Max {item.max_marks}
                  </option>
                ))}
              </select>
            </div>

            <div className="field field-span-2">
              <label htmlFor="marks-search">Search student</label>
              <input
                id="marks-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by student name or student code"
              />
            </div>
          </div>

          {selectedExam ? (
            <div className="detail-stack">
              <div>
                <span className="field-note">Class scope</span>
                <strong>
                  {selectedExam.class_name}
                  {selectedExam.section_name ? ` / ${selectedExam.section_name}` : " / Whole class"}
                </strong>
              </div>
              <div>
                <span className="field-note">Date window</span>
                <strong>
                  {selectedExam.start_date} to {selectedExam.end_date}
                </strong>
              </div>
              <div>
                <span className="field-note">Status</span>
                <strong>{selectedExam.status}</strong>
              </div>
            </div>
          ) : null}
        </Panel>

        <Panel title="Student register" subtitle="Fill marks, set absent status, and add remarks. Published exams stay read-only in the backend.">
          <div className="form-actions">
            <button className="ghost-button" type="button" disabled={!selectedExamSubjectId || registerLoading} onClick={loadRegister}>
              Refresh register
            </button>
            <button className="primary-button" type="button" disabled={!selectedExamSubjectId || submitting} onClick={handleSave}>
              {submitting ? "Saving..." : "Save marks"}
            </button>
          </div>

          <DataTable<MarkRegisterRow>
            rows={registerRows}
            emptyMessage={
              loading || registerLoading
                ? "Loading marks register..."
                : selectedExamSubjectId
                  ? "No students are available for this exam scope."
                  : "Choose an exam subject to open the marks register."
            }
            columns={[
              {
                key: "student",
                label: "Student",
                render: (row) => (
                  <div className="field-stack">
                    <strong>{row.student_name}</strong>
                    <span className="panel-note">{row.student_code || "Student code pending"}</span>
                  </div>
                ),
              },
              {
                key: "marks",
                label: "Marks",
                render: (row) => (
                  <input
                    className="table-note-input"
                    type="number"
                    min="0"
                    step="0.01"
                    value={drafts[row.student_id]?.marks_obtained || ""}
                    disabled={drafts[row.student_id]?.is_absent}
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      updateDraft(row.student_id, { marks_obtained: event.target.value })
                    }
                  />
                ),
              },
              {
                key: "absent",
                label: "Absent",
                render: (row) => (
                  <label className="inline-check">
                    <input
                      type="checkbox"
                      checked={Boolean(drafts[row.student_id]?.is_absent)}
                      onChange={(event) =>
                        updateDraft(row.student_id, {
                          is_absent: event.target.checked,
                          marks_obtained: event.target.checked ? "" : drafts[row.student_id]?.marks_obtained || "",
                        })
                      }
                    />
                    <span>{drafts[row.student_id]?.is_absent ? "Absent" : "Present"}</span>
                  </label>
                ),
              },
              {
                key: "remark",
                label: "Remark",
                render: (row) => (
                  <input
                    className="table-note-input"
                    value={drafts[row.student_id]?.remark || ""}
                    onChange={(event: ChangeEvent<HTMLInputElement>) => updateDraft(row.student_id, { remark: event.target.value })}
                    placeholder="Optional note"
                  />
                ),
              },
            ]}
          />
        </Panel>
      </section>
    </AcademicWorkspace>
  );
}
