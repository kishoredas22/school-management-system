import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatDate } from "../lib/format";
import type {
  AcademicYear,
  AttendanceStatus,
  ClassRoom,
  Section,
  StudentAttendanceRegisterItem,
  Teacher,
  TeacherAttendanceRecord,
} from "../types";

type AttendanceMode = "students" | "teachers";

const today = new Date().toISOString().slice(0, 10);

function formatTodayLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function AttendancePage() {
  const { session, logout } = useAuth();
  const [mode, setMode] = useState<AttendanceMode>("students");
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [studentRegister, setStudentRegister] = useState<StudentAttendanceRegisterItem[]>([]);
  const [teacherAttendance, setTeacherAttendance] = useState<TeacherAttendanceRecord[]>([]);
  const [studentSearch, setStudentSearch] = useState("");
  const [teacherSearch, setTeacherSearch] = useState("");
  const [studentForm, setStudentForm] = useState({
    class_id: "",
    section_id: "",
    date: today,
  });
  const [teacherForm, setTeacherForm] = useState({
    teacher_id: "",
    date: today,
    status: "PRESENT" as AttendanceStatus,
    note: "",
  });
  const [studentStatuses, setStudentStatuses] = useState<Record<string, AttendanceStatus>>({});
  const [loading, setLoading] = useState(true);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!session) {
      return;
    }

    const token = session.accessToken;
    const role = session.role;
    let isMounted = true;

    async function loadReferences() {
      try {
        const [years, classList, sectionList, teacherList] = await Promise.all([
          apiRequest<AcademicYear[]>("/academic-years", { token }),
          apiRequest<ClassRoom[]>("/reference/classes", { token }),
          apiRequest<Section[]>("/reference/sections", { token }),
          role === "TEACHER"
            ? Promise.resolve([])
            : apiRequest<Teacher[]>("/teachers", { token }),
        ]);

        if (!isMounted) {
          return;
        }

        setAcademicYears(years);
        setClasses(classList);
        setSections(sectionList);
        setTeachers(teacherList);
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

    loadReferences();

    return () => {
      isMounted = false;
    };
  }, [logout, session]);

  useEffect(() => {
    if (!session || !studentForm.class_id || !studentForm.section_id || !studentForm.date) {
      setStudentRegister([]);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadRegister() {
      setRegisterLoading(true);
      try {
        const params = new URLSearchParams({
          class_id: studentForm.class_id,
          section_id: studentForm.section_id,
          date: studentForm.date,
        });
        if (studentSearch.trim()) {
          params.set("q", studentSearch.trim());
        }

        const data = await apiRequest<StudentAttendanceRegisterItem[]>(`/attendance/students?${params.toString()}`, {
          token,
        });

        if (!isMounted) {
          return;
        }

        setStudentRegister(data);
        setStudentStatuses((current) =>
          Object.fromEntries(
            data.map((student) => [student.student_id, student.status || current[student.student_id] || "PRESENT"]),
          ),
        );
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
          setRegisterLoading(false);
        }
      }
    }

    loadRegister();

    return () => {
      isMounted = false;
    };
  }, [logout, session, studentForm.class_id, studentForm.section_id, studentForm.date, studentSearch]);

  useEffect(() => {
    if (!session || session.role === "TEACHER" || !teacherForm.date) {
      setTeacherAttendance([]);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadTeacherAttendance() {
      try {
        const data = await apiRequest<TeacherAttendanceRecord[]>(`/attendance/teachers?date=${teacherForm.date}`, { token });

        if (isMounted) {
          setTeacherAttendance(data);
        }
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

    loadTeacherAttendance();

    return () => {
      isMounted = false;
    };
  }, [logout, session, teacherForm.date]);

  const activeYear = academicYears.find((item) => item.is_active) || academicYears[0] || null;
  const visibleSections = sections.filter(
    (section) => !studentForm.class_id || section.class_id === studentForm.class_id,
  );
  const filteredTeachers = teachers.filter((teacher) =>
    `${teacher.name} ${teacher.phone || ""}`.toLowerCase().includes(teacherSearch.trim().toLowerCase()),
  );

  async function handleStudentAttendanceSubmit() {
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const response = await apiRequest<{ count: number }>("/attendance/students", {
        method: "POST",
        token: session.accessToken,
        body: {
          class_id: studentForm.class_id,
          section_id: studentForm.section_id,
          date: studentForm.date,
          attendance: studentRegister.map((student) => ({
            student_id: student.student_id,
            status: studentStatuses[student.student_id] || "PRESENT",
          })),
        },
      });
      setMessage(`Student attendance saved for ${response.count} student(s). Re-open this date to revise later.`);
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

  async function handleTeacherAttendanceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/attendance/teachers", {
        method: "POST",
        token: session.accessToken,
        body: {
          teacher_id: teacherForm.teacher_id,
          date: teacherForm.date,
          status: teacherForm.status,
          note: teacherForm.note || null,
        },
      });

      const refreshed = await apiRequest<TeacherAttendanceRecord[]>(`/attendance/teachers?date=${teacherForm.date}`, {
        token: session.accessToken,
      });

      setTeacherAttendance(refreshed);
      setMessage("Teacher attendance recorded and the daily register has been refreshed.");
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
        eyebrow="Daily register"
        title="Attendance"
        description="Daily attendance always writes into the active academic year. Load a date, review saved entries, update them, and submit the final register from the list itself."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <div className="segmented">
        <button className={mode === "students" ? "is-active" : ""} type="button" onClick={() => setMode("students")}>
          Students
        </button>
        {session?.role !== "TEACHER" ? (
          <button className={mode === "teachers" ? "is-active" : ""} type="button" onClick={() => setMode("teachers")}>
            Teachers
          </button>
        ) : null}
      </div>

      <div className="today-chip">
        <span className="today-orb">{new Date(today).getDate()}</span>
        <div>
          <span className="field-note">Today focus</span>
          <strong>{formatTodayLabel(today)}</strong>
        </div>
        <span className="chip">Future attendance is blocked</span>
      </div>

      {mode === "students" ? (
        <section className="split-grid">
          <Panel
            title="Student attendance context"
            subtitle="Pick the class, section, and date. The register below loads existing saved statuses so you can correct the same day later."
          >
            <div className="detail-stack">
              <div>
                <span className="field-note">Active academic year</span>
                <strong>{activeYear?.name || "No active year"}</strong>
              </div>
              <div>
                <span className="field-note">Register size</span>
                <strong>{registerLoading ? "Loading..." : String(studentRegister.length)}</strong>
              </div>
            </div>

            <div className="form-grid">
              <div className="field">
                <label htmlFor="attendance-class">Class</label>
                <select
                  id="attendance-class"
                  value={studentForm.class_id}
                  onChange={(event) =>
                    setStudentForm((current) => ({
                      ...current,
                      class_id: event.target.value,
                      section_id: "",
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
                <label htmlFor="attendance-section">Section</label>
                <select
                  id="attendance-section"
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

              <div className="field">
                <label htmlFor="attendance-date">Date</label>
                <input
                  id="attendance-date"
                  type="date"
                  value={studentForm.date}
                  max={today}
                  onChange={(event) => setStudentForm((current) => ({ ...current, date: event.target.value }))}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="attendance-search">Search student</label>
                <input
                  id="attendance-search"
                  value={studentSearch}
                  onChange={(event) => setStudentSearch(event.target.value)}
                  placeholder="Search by student name or code"
                />
              </div>
            </div>
          </Panel>

          <Panel title="Editable register" subtitle="Statuses default to PRESENT for new rows and preserve saved values for existing dates.">
            {studentRegister.length ? (
              <>
                <div className="check-list">
                  {studentRegister.map((student) => (
                    <div className="attendance-row" key={student.student_id}>
                      <div>
                        <strong>{student.student_name}</strong>
                        <div className="field-note">
                          {student.student_code || "Student code pending"}
                          {student.status ? ` | Saved as ${student.status}` : " | New row"}
                        </div>
                      </div>
                      <select
                        value={studentStatuses[student.student_id] || "PRESENT"}
                        onChange={(event) =>
                          setStudentStatuses((current) => ({
                            ...current,
                            [student.student_id]: event.target.value as AttendanceStatus,
                          }))
                        }
                      >
                        <option value="PRESENT">PRESENT</option>
                        <option value="ABSENT">ABSENT</option>
                        <option value="LEAVE">LEAVE</option>
                      </select>
                    </div>
                  ))}
                </div>

                <div className="form-actions register-actions">
                  <span className="field-note">
                    Review the register, then submit from here. You can reopen the same date again within the edit window.
                  </span>
                  <button
                    className="accent-button"
                    type="button"
                    disabled={submitting || !studentRegister.length || !studentForm.section_id}
                    onClick={handleStudentAttendanceSubmit}
                  >
                    {submitting ? "Saving..." : "Submit student attendance"}
                  </button>
                </div>
              </>
            ) : (
              <div className="empty-state">
                {loading || registerLoading
                  ? "Loading attendance register..."
                  : "Choose a class, section, and date to load students for attendance."}
              </div>
            )}
          </Panel>
        </section>
      ) : (
        <Panel title="Teacher attendance" subtitle="Record teacher attendance, then verify the saved rows for the selected date in the table below.">
          <form className="field-stack" onSubmit={handleTeacherAttendanceSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="teacher-attendance-search">Search teacher</label>
                <input
                  id="teacher-attendance-search"
                  value={teacherSearch}
                  onChange={(event) => setTeacherSearch(event.target.value)}
                  placeholder="Search by teacher name or phone"
                />
              </div>

              <div className="field">
                <label htmlFor="teacher-attendance-teacher">Teacher</label>
                <select
                  id="teacher-attendance-teacher"
                  value={teacherForm.teacher_id}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, teacher_id: event.target.value }))}
                  required
                >
                  <option value="">Select teacher</option>
                  {filteredTeachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="teacher-attendance-date">Date</label>
                <input
                  id="teacher-attendance-date"
                  type="date"
                  value={teacherForm.date}
                  max={today}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, date: event.target.value }))}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="teacher-attendance-status">Status</label>
                <select
                  id="teacher-attendance-status"
                  value={teacherForm.status}
                  onChange={(event) =>
                    setTeacherForm((current) => ({ ...current, status: event.target.value as AttendanceStatus }))
                  }
                >
                  <option value="PRESENT">PRESENT</option>
                  <option value="ABSENT">ABSENT</option>
                  <option value="LEAVE">LEAVE</option>
                </select>
              </div>

              <div className="field field-span-2">
                <label htmlFor="teacher-attendance-note">Note</label>
                <input
                  id="teacher-attendance-note"
                  value={teacherForm.note}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, note: event.target.value }))}
                  placeholder="Optional note for the selected teacher"
                />
              </div>
            </div>

            <div className="form-actions">
              <button className="accent-button" type="submit" disabled={submitting || session?.role === "TEACHER"}>
                {submitting ? "Saving..." : "Submit teacher attendance"}
              </button>
            </div>
          </form>

          <DataTable
            rows={teacherAttendance}
            emptyMessage="No teacher attendance has been recorded for the selected date yet."
            columns={[
              {
                key: "teacher",
                label: "Teacher",
                render: (row) => row.teacher_name,
              },
              {
                key: "date",
                label: "Date",
                render: (row) => formatDate(row.attendance_date),
              },
              {
                key: "status",
                label: "Status",
                render: (row) => (
                  <div className={`status-pill status-${row.status.toLowerCase()}`}>{row.status}</div>
                ),
              },
              {
                key: "note",
                label: "Note",
                render: (row) => row.note || "No note",
              },
            ]}
          />
        </Panel>
      )}
    </>
  );
}
