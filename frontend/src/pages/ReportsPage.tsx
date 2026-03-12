import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { DataTable } from "../components/DataTable";
import { MetricCard } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { downloadFile, apiRequest } from "../lib/api";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { getErrorMessage } from "../lib/errors";
import { formatCurrency, formatDate, fullName, monthOptions } from "../lib/format";
import type {
  AcademicYear,
  AttendanceDetail,
  AttendanceSummary,
  ClassFeeBalance,
  DashboardOverview,
  MonthlyFinanceTrendPoint,
  Paginated,
  PendingFeeItem,
  StudentRecord,
  StudentStatusBreakdown,
  TeacherPaymentSummary,
} from "../types";

export function ReportsPage() {
  const { session, logout } = useAuth();
  const currentDate = new Date();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [students, setStudents] = useState<StudentRecord[]>([]);
  const [studentSearch, setStudentSearch] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [month, setMonth] = useState(currentDate.getMonth() + 1);
  const [calendarYear, setCalendarYear] = useState(currentDate.getFullYear());
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [pendingFees, setPendingFees] = useState<PendingFeeItem[]>([]);
  const [attendanceSummary, setAttendanceSummary] = useState<AttendanceSummary[]>([]);
  const [attendanceDetails, setAttendanceDetails] = useState<AttendanceDetail[]>([]);
  const [teacherPayments, setTeacherPayments] = useState<TeacherPaymentSummary[]>([]);
  const [financeTrend, setFinanceTrend] = useState<MonthlyFinanceTrendPoint[]>([]);
  const [studentStatuses, setStudentStatuses] = useState<StudentStatusBreakdown[]>([]);
  const [classFeeBalance, setClassFeeBalance] = useState<ClassFeeBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const deferredStudentSearch = useDeferredValue(studentSearch);

  useEffect(() => {
    if (!session) {
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadYears() {
      try {
        const years = await apiRequest<AcademicYear[]>("/academic-years", {
          token,
        });
        if (!isMounted) {
          return;
        }
        setAcademicYears(years);
        const activeYear = years.find((item) => item.is_active) || years[0];
        setYearFilter(activeYear?.id || "");
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

    loadYears();

    return () => {
      isMounted = false;
    };
  }, [logout, session]);

  useEffect(() => {
    if (!session || !yearFilter) {
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadStudents() {
      try {
        const studentPage = await apiRequest<Paginated<StudentRecord>>(
          `/students?year_id=${yearFilter}&page=1&size=100&include_inactive=true`,
          {
            token,
          },
        );
        if (!isMounted) {
          return;
        }
        setStudents(studentPage.data);
        setSelectedStudentId((current) =>
          studentPage.data.some((student) => student.id === current) ? current : studentPage.data[0]?.id || "",
        );
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

    loadStudents();

    return () => {
      isMounted = false;
    };
  }, [logout, session, yearFilter]);

  useEffect(() => {
    if (!session || !yearFilter) {
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadReports() {
      setLoading(true);
      setError("");

      try {
        const [dashboardData, pending, attendance, payroll, trend, statuses, classBalance] = await Promise.all([
          apiRequest<DashboardOverview>(`/reports/dashboard?year_id=${yearFilter}`, {
            token,
          }),
          apiRequest<PendingFeeItem[]>(`/reports/fees/pending?year_id=${yearFilter}`, {
            token,
          }),
          apiRequest<AttendanceSummary[]>(
            `/reports/attendance/students?month=${month}&year=${calendarYear}&year_id=${yearFilter}`,
            {
              token,
            },
          ),
          apiRequest<TeacherPaymentSummary[]>(`/reports/teacher-payments?year_id=${yearFilter}`, {
            token,
          }),
          apiRequest<MonthlyFinanceTrendPoint[]>(
            `/reports/finance/trend?calendar_year=${calendarYear}&year_id=${yearFilter}`,
            {
              token,
            },
          ),
          apiRequest<StudentStatusBreakdown[]>(`/reports/students/status?year_id=${yearFilter}`, {
            token,
          }),
          apiRequest<ClassFeeBalance[]>(`/reports/fees/pending/by-class?year_id=${yearFilter}`, {
            token,
          }),
        ]);

        if (!isMounted) {
          return;
        }

        setOverview(dashboardData);
        setPendingFees(pending);
        setAttendanceSummary(attendance);
        setTeacherPayments(payroll);
        setFinanceTrend(trend);
        setStudentStatuses(statuses);
        setClassFeeBalance(classBalance);
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

    loadReports();

    return () => {
      isMounted = false;
    };
  }, [calendarYear, logout, month, session, yearFilter]);

  useEffect(() => {
    if (!session || !selectedStudentId) {
      setAttendanceDetails([]);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadAttendanceDetails() {
      try {
        const data = await apiRequest<AttendanceDetail[]>(
          `/reports/attendance/details?student_id=${selectedStudentId}&month=${month}&year=${calendarYear}`,
          {
            token,
          },
        );
        if (isMounted) {
          setAttendanceDetails(data);
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

    loadAttendanceDetails();

    return () => {
      isMounted = false;
    };
  }, [calendarYear, logout, month, selectedStudentId, session]);

  const filteredStudents = useMemo(() => students.filter((student) => {
    const term = deferredStudentSearch.trim().toLowerCase();
    if (!term) {
      return true;
    }
    return `${student.first_name} ${student.last_name || ""} ${student.student_id || ""}`.toLowerCase().includes(term);
  }), [deferredStudentSearch, students]);

  async function handleExport(path: string, filename: string) {
    if (!session) {
      return;
    }

    setMessage("");
    setError("");
    try {
      await downloadFile(path, session.accessToken, filename);
      setMessage(`Export ready: ${filename}`);
    } catch (downloadError) {
      if (isUnauthorizedError(downloadError)) {
        logout();
        return;
      }
      setError(getErrorMessage(downloadError));
    }
  }

  return (
    <>
      <PageIntro
        eyebrow="Management reports"
        title="Reports"
        description="Finance, attendance, and payroll views now include export-ready data sets, monthly trend tracking, and class-level pressure points for faster operational review."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <Panel title="Report filters" subtitle="These selectors control the report set shown below.">
        <div className="form-grid">
          <div className="field">
            <label htmlFor="report-year-filter">Academic year</label>
            <select id="report-year-filter" value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
              <option value="">Select year</option>
              {academicYears.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="report-month">Month</label>
            <select id="report-month" value={month} onChange={(event) => setMonth(Number(event.target.value))}>
              {monthOptions().map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="report-calendar-year">Calendar year</label>
            <input
              id="report-calendar-year"
              type="number"
              min="2000"
              max="2100"
              value={calendarYear}
              onChange={(event) => setCalendarYear(Number(event.target.value))}
            />
          </div>
          <div className="field field-span-2">
            <label htmlFor="report-student-search">Search attendance student</label>
            <input
              id="report-student-search"
              value={studentSearch}
              onChange={(event) => setStudentSearch(event.target.value)}
              placeholder="Search by student name or student code"
            />
          </div>
          <div className="field field-span-2">
            <label htmlFor="report-student">Attendance detail student</label>
            <select
              id="report-student"
              value={selectedStudentId}
              onChange={(event) => setSelectedStudentId(event.target.value)}
            >
              <option value="">Select student</option>
              {filteredStudents.map((student) => (
                <option key={student.id} value={student.id}>
                  {fullName(student.first_name, student.last_name)} | {student.student_id || "Pending ID"}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Panel>

      <section className="metric-grid">
        <MetricCard
          label="Fees collected"
          value={loading ? "..." : formatCurrency(overview?.fee_collected || 0)}
          detail="Selected academic year collection total"
          tone="ink"
        />
        <MetricCard
          label="Pending fees"
          value={loading ? "..." : formatCurrency(overview?.fee_pending || 0)}
          detail={`${overview?.pending_students || 0} students still outstanding`}
          tone="coral"
        />
        <MetricCard
          label="Active students"
          value={loading ? "..." : String(overview?.active_students || 0)}
          detail={`${overview?.student_total || 0} students in the current reporting scope`}
          tone="sand"
        />
        <MetricCard
          label="Salary pending"
          value={loading ? "..." : formatCurrency(overview?.salary_pending || 0)}
          detail={`${overview?.teacher_total || 0} teachers tracked across payroll`}
          tone="mint"
        />
      </section>

      <section className="stack-grid">
        <Panel title="Monthly finance trend" subtitle="Fee collection versus teacher payouts by calendar month.">
          <DataTable
            rows={financeTrend}
            emptyMessage="No finance trend data available for the current filter."
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
              {
                key: "net",
                label: "Net cashflow",
                render: (row) => formatCurrency(row.net_cashflow),
              },
            ]}
          />
        </Panel>

        <Panel title="Student status breakdown" subtitle="Current student lifecycle mix in the selected academic year.">
          <DataTable
            rows={studentStatuses}
            emptyMessage="No student status data available."
            columns={[
              {
                key: "status",
                label: "Status",
                render: (row) => row.status.replace(/_/g, " "),
              },
              {
                key: "count",
                label: "Students",
                render: (row) => row.count,
              },
            ]}
          />
        </Panel>
      </section>

      <section className="stack-grid">
        <Panel title="Fee pending report" subtitle="Students still carrying a fee balance in the selected academic year.">
          <div className="toolbar">
            <button
              className="ghost-button"
              type="button"
              onClick={() =>
                handleExport(`/reports/fees/pending/export?year_id=${yearFilter}`, "pending-fees.csv")
              }
            >
              Export CSV
            </button>
          </div>
          <DataTable
            rows={pendingFees}
            emptyMessage="No pending fee balances for the current filter."
            columns={[
              {
                key: "student",
                label: "Student",
                render: (row) => (
                  <div>
                    <strong>{row.student_name}</strong>
                    <div className="field-note">{row.class_name}</div>
                  </div>
                ),
              },
              {
                key: "fee",
                label: "Total fee",
                render: (row) => formatCurrency(row.total_fee),
              },
              {
                key: "paid",
                label: "Paid",
                render: (row) => formatCurrency(row.total_paid),
              },
              {
                key: "pending",
                label: "Pending",
                render: (row) => formatCurrency(row.pending),
              },
            ]}
          />
        </Panel>

        <Panel title="Class fee pressure" subtitle="Pending balances grouped by class to spot where follow-up is needed most.">
          <DataTable
            rows={classFeeBalance}
            emptyMessage="No class fee balance data available."
            columns={[
              {
                key: "class",
                label: "Class",
                render: (row) => row.class_name,
              },
              {
                key: "students",
                label: "Students pending",
                render: (row) => row.student_count,
              },
              {
                key: "collected",
                label: "Collected",
                render: (row) => formatCurrency(row.collected_total),
              },
              {
                key: "pending",
                label: "Pending",
                render: (row) => formatCurrency(row.pending_total),
              },
            ]}
          />
        </Panel>
      </section>

      <section className="stack-grid">
        <Panel title="Teacher payment report" subtitle="Contract totals and outstanding salary balances.">
          <div className="toolbar">
            <button
              className="ghost-button"
              type="button"
              onClick={() =>
                handleExport(`/reports/teacher-payments/export?year_id=${yearFilter}`, "teacher-payments.csv")
              }
            >
              Export CSV
            </button>
          </div>
          <DataTable
            rows={teacherPayments}
            emptyMessage="No teacher payment data available."
            columns={[
              {
                key: "teacher",
                label: "Teacher",
                render: (row) => row.teacher_name,
              },
              {
                key: "contract",
                label: "Contract total",
                render: (row) => formatCurrency(row.contract_total),
              },
              {
                key: "paid",
                label: "Paid",
                render: (row) => formatCurrency(row.total_paid),
              },
              {
                key: "balance",
                label: "Pending balance",
                render: (row) => formatCurrency(row.pending_balance),
              },
            ]}
          />
        </Panel>

        <Panel title="Attendance detail" subtitle="Day-level detail for the selected student and month.">
          <DataTable
            rows={attendanceDetails}
            emptyMessage="Select a student to load daily attendance detail."
            columns={[
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
            ]}
          />
        </Panel>
      </section>

      <Panel title="Student attendance summary" subtitle="Monthly summary counts with percentage present.">
        <div className="toolbar">
          <button
            className="ghost-button"
            type="button"
            onClick={() =>
              handleExport(
                `/reports/attendance/students/export?month=${month}&year=${calendarYear}&year_id=${yearFilter}`,
                "student-attendance.csv",
              )
            }
          >
            Export CSV
          </button>
        </div>
        <DataTable
          rows={attendanceSummary}
          emptyMessage="No attendance summary data available."
          columns={[
            {
              key: "student",
              label: "Student",
              render: (row) => row.entity_name,
            },
            {
              key: "present",
              label: "Present",
              render: (row) => row.present_count,
            },
            {
              key: "absent",
              label: "Absent",
              render: (row) => row.absent_count,
            },
            {
              key: "leave",
              label: "Leave",
              render: (row) => row.leave_count,
            },
            {
              key: "percent",
              label: "Attendance %",
              render: (row) => `${row.attendance_percentage}%`,
            },
          ]}
        />
      </Panel>
    </>
  );
}
