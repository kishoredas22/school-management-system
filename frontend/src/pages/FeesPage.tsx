import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { MetricCard } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest, downloadFile } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatCurrency, formatDate, fullName } from "../lib/format";
import type { AcademicYear, ClassRoom, FeeStructure, FeeSummary, FeeType, Paginated, PaymentMode, StudentRecord } from "../types";

const emptyStructureForm = {
  class_id: "",
  academic_year_id: "",
  fee_name: "",
  amount: "",
  fee_type: "ONE_TIME" as FeeType,
};

const emptyPaymentForm = {
  student_id: "",
  fee_structure_id: "",
  amount: "",
  payment_mode: "CASH" as PaymentMode,
  payment_date: "",
};

const today = new Date().toISOString().slice(0, 10);

export function FeesPage() {
  const { session, logout } = useAuth();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [students, setStudents] = useState<StudentRecord[]>([]);
  const [catalogStructures, setCatalogStructures] = useState<FeeStructure[]>([]);
  const [paymentStructures, setPaymentStructures] = useState<FeeStructure[]>([]);
  const [feeSummary, setFeeSummary] = useState<FeeSummary | null>(null);
  const [structureForm, setStructureForm] = useState(emptyStructureForm);
  const [paymentForm, setPaymentForm] = useState(emptyPaymentForm);
  const [studentSearch, setStudentSearch] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [lastReceipt, setLastReceipt] = useState<{ paymentId: string; receiptNumber: string } | null>(null);

  const canManageStructures = session?.role === "SUPER_ADMIN" || session?.role === "ADMIN";

  useEffect(() => {
    if (!session) {
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadReferences() {
      setLoading(true);
      try {
        const [years, classList] = await Promise.all([
          apiRequest<AcademicYear[]>("/academic-years", { token }),
          apiRequest<ClassRoom[]>("/reference/classes", { token }),
        ]);
        if (!isMounted) {
          return;
        }
        const activeYear = years.find((item) => item.is_active) || years[0];
        setAcademicYears(years);
        setClasses(classList);
        setYearFilter(activeYear?.id || "");
        setStructureForm((current) => ({ ...current, academic_year_id: activeYear?.id || "" }));
        setPaymentForm((current) => ({
          ...current,
          payment_date: current.payment_date || today,
        }));
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
    if (!session || !yearFilter) {
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadStudentsForYear() {
      try {
        const data = await apiRequest<Paginated<StudentRecord>>(
          `/students?year_id=${yearFilter}&page=1&size=100&include_inactive=true`,
          {
            token,
          },
        );
        if (!isMounted) {
          return;
        }
        setStudents(data.data);
        setPaymentForm((current) => ({
          ...current,
          student_id: data.data.some((student) => student.id === current.student_id) ? current.student_id : "",
          fee_structure_id: "",
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

    loadStudentsForYear();

    return () => {
      isMounted = false;
    };
  }, [logout, session, yearFilter]);

  useEffect(() => {
    if (!session || !structureForm.class_id || !structureForm.academic_year_id) {
      setCatalogStructures([]);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadCatalog() {
      try {
        const data = await apiRequest<FeeStructure[]>(
          `/fees/structures?class_id=${structureForm.class_id}&year_id=${structureForm.academic_year_id}`,
          {
            token,
          },
        );
        if (isMounted) {
          setCatalogStructures(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getErrorMessage(loadError));
        }
      }
    }

    loadCatalog();

    return () => {
      isMounted = false;
    };
  }, [session, structureForm.academic_year_id, structureForm.class_id]);

  const selectedStudent = students.find((student) => student.id === paymentForm.student_id) || null;
  const selectedStudentClassId = selectedStudent?.class_id || "";
  const filteredStudents = students.filter((student) => {
    const term = studentSearch.trim().toLowerCase();
    if (!term) {
      return true;
    }
    return `${student.first_name} ${student.last_name || ""} ${student.student_id || ""}`.toLowerCase().includes(term);
  });

  useEffect(() => {
    if (!session || !selectedStudentClassId || !yearFilter) {
      setPaymentStructures([]);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadStructuresForPayment() {
      try {
        const data = await apiRequest<FeeStructure[]>(
          `/fees/structures?class_id=${selectedStudentClassId}&year_id=${yearFilter}`,
          {
            token,
          },
        );
        if (isMounted) {
          setPaymentStructures(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getErrorMessage(loadError));
        }
      }
    }

    loadStructuresForPayment();

    return () => {
      isMounted = false;
    };
  }, [selectedStudentClassId, session, yearFilter]);

  useEffect(() => {
    if (!session || !paymentForm.student_id || !yearFilter) {
      setFeeSummary(null);
      return;
    }

    const token = session.accessToken;
    let isMounted = true;

    async function loadSummary() {
      try {
        const data = await apiRequest<FeeSummary>(
          `/fees/payments/student/${paymentForm.student_id}?year_id=${yearFilter}`,
          {
            token,
          },
        );
        if (isMounted) {
          setFeeSummary(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setFeeSummary(null);
          setError(getErrorMessage(loadError));
        }
      }
    }

    loadSummary();

    return () => {
      isMounted = false;
    };
  }, [paymentForm.student_id, session, yearFilter]);

  async function handleStructureSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/fees/structures", {
        method: "POST",
        token: session.accessToken,
        body: {
          class_id: structureForm.class_id,
          academic_year_id: structureForm.academic_year_id,
          fee_name: structureForm.fee_name,
          amount: structureForm.amount,
          fee_type: structureForm.fee_type,
        },
      });
      setMessage("Fee structure created.");
      setStructureForm((current) => ({
        ...current,
        fee_name: "",
        amount: "",
        fee_type: "ONE_TIME",
      }));
      const refreshed = await apiRequest<FeeStructure[]>(
        `/fees/structures?class_id=${structureForm.class_id}&year_id=${structureForm.academic_year_id}`,
        {
          token: session.accessToken,
        },
      );
      setCatalogStructures(refreshed);
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

  async function handlePaymentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const response = await apiRequest<{ id: string; receipt_number: string }>("/fees/payments", {
        method: "POST",
        token: session.accessToken,
        body: {
          student_id: paymentForm.student_id,
          fee_structure_id: paymentForm.fee_structure_id,
          amount: paymentForm.amount,
          payment_mode: paymentForm.payment_mode,
          payment_date: paymentForm.payment_date,
        },
      });
      setLastReceipt({ paymentId: response.id, receiptNumber: response.receipt_number });
      setMessage(`Fee payment recorded. Receipt ${response.receipt_number} is available.`);
      setPaymentForm((current) => ({
        ...current,
        fee_structure_id: "",
        amount: "",
      }));
      if (paymentForm.student_id) {
        const summary = await apiRequest<FeeSummary>(
          `/fees/payments/student/${paymentForm.student_id}?year_id=${yearFilter}`,
          {
            token: session.accessToken,
          },
        );
        setFeeSummary(summary);
      }
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

  async function downloadReceipt(paymentId: string, receiptNumber: string) {
    if (!session) {
      return;
    }

    try {
      await downloadFile(`/fees/payments/${paymentId}/receipt`, session.accessToken, `${receiptNumber}.pdf`);
    } catch (downloadError) {
      setError(getErrorMessage(downloadError));
    }
  }

  return (
    <>
      <PageIntro
        eyebrow="Finance operations"
        title="Fees"
        description="Create academic-year fee structures, collect payments, and inspect live student fee summaries with searchable student selection."
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="metric-grid">
        <MetricCard
          label="Academic year"
          value={academicYears.find((item) => item.id === yearFilter)?.name || "Not set"}
          detail="Selector driving fee lookups and student summaries"
          tone="sand"
        />
        <MetricCard
          label="Students loaded"
          value={loading ? "..." : String(students.length)}
          detail="Student set fetched for the selected academic year"
          tone="mint"
        />
        <MetricCard
          label="Fee total"
          value={formatCurrency(feeSummary?.total_fee || 0)}
          detail="Only for the currently selected student"
          tone="ink"
        />
        <MetricCard
          label="Pending balance"
          value={formatCurrency(feeSummary?.pending || 0)}
          detail="Updates after each recorded payment"
          tone="coral"
        />
      </section>

      <Panel title="Finance context" subtitle="Choose the academic year that drives student and structure lookups.">
        <div className="form-grid">
          <div className="field">
            <label htmlFor="fee-year-filter">Academic year</label>
            <select id="fee-year-filter" value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
              <option value="">Select year</option>
              {academicYears.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Panel>

      <section className="split-grid">
        <Panel
          title="Fee structure studio"
          subtitle={
            canManageStructures
              ? "Define class-level structures for an academic year."
              : "Your role can review payment structures but cannot create them."
          }
        >
          {canManageStructures ? (
            <form className="field-stack" onSubmit={handleStructureSubmit}>
              <div className="form-grid">
                <div className="field">
                  <label htmlFor="structure-class">Class</label>
                  <select
                    id="structure-class"
                    value={structureForm.class_id}
                    onChange={(event) => setStructureForm((current) => ({ ...current, class_id: event.target.value }))}
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
                  <label htmlFor="structure-year">Academic year</label>
                  <select
                    id="structure-year"
                    value={structureForm.academic_year_id}
                    onChange={(event) =>
                      setStructureForm((current) => ({ ...current, academic_year_id: event.target.value }))
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
                  <label htmlFor="structure-name">Fee name</label>
                  <input
                    id="structure-name"
                    value={structureForm.fee_name}
                    onChange={(event) => setStructureForm((current) => ({ ...current, fee_name: event.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="structure-amount">Amount</label>
                  <input
                    id="structure-amount"
                    type="number"
                    step="0.01"
                    value={structureForm.amount}
                    onChange={(event) => setStructureForm((current) => ({ ...current, amount: event.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="structure-type">Fee type</label>
                  <select
                    id="structure-type"
                    value={structureForm.fee_type}
                    onChange={(event) =>
                      setStructureForm((current) => ({ ...current, fee_type: event.target.value as FeeType }))
                    }
                  >
                    <option value="ONE_TIME">One Time</option>
                    <option value="RECURRING">Recurring</option>
                  </select>
                </div>
              </div>

              <div className="form-actions">
                <button className="accent-button" type="submit" disabled={submitting}>
                  Create fee structure
                </button>
              </div>
            </form>
          ) : null}

          <DataTable
            rows={catalogStructures}
            emptyMessage="Select a class and year to view fee structures."
            columns={[
              {
                key: "name",
                label: "Fee",
                render: (row) => (
                  <div>
                    <strong>{row.fee_name}</strong>
                    <div className="field-note">{row.fee_type.replace(/_/g, " ")}</div>
                  </div>
                ),
              },
              {
                key: "amount",
                label: "Amount",
                render: (row) => formatCurrency(row.amount),
              },
              {
                key: "status",
                label: "Active",
                render: (row) => (
                  <div className={`status-pill ${row.is_active ? "status-active" : "status-inactive"}`}>
                    {row.is_active ? "Active" : "Inactive"}
                  </div>
                ),
              },
            ]}
          />
        </Panel>

        <Panel title="Collect payment" subtitle="Choose a student, then record a payment against a matching fee structure.">
          <form className="field-stack" onSubmit={handlePaymentSubmit}>
            <div className="form-grid">
              <div className="field field-span-2">
                <label htmlFor="payment-student-search">Search student</label>
                <input
                  id="payment-student-search"
                  value={studentSearch}
                  onChange={(event) => setStudentSearch(event.target.value)}
                  placeholder="Search by student name or code"
                />
              </div>
              <div className="field">
                <label htmlFor="payment-student">Student</label>
                <select
                  id="payment-student"
                  value={paymentForm.student_id}
                  onChange={(event) =>
                    setPaymentForm((current) => ({
                      ...current,
                      student_id: event.target.value,
                      fee_structure_id: "",
                    }))
                  }
                  required
                >
                  <option value="">Select student</option>
                  {filteredStudents.map((student) => (
                    <option key={student.id} value={student.id}>
                      {fullName(student.first_name, student.last_name)} | {student.student_id || "Pending ID"} | {student.class_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="payment-structure">Fee structure</label>
                <select
                  id="payment-structure"
                  value={paymentForm.fee_structure_id}
                  onChange={(event) =>
                    setPaymentForm((current) => ({ ...current, fee_structure_id: event.target.value }))
                  }
                  required
                >
                  <option value="">Select structure</option>
                  {paymentStructures.map((structure) => (
                    <option key={structure.id} value={structure.id}>
                      {structure.fee_name} | {formatCurrency(structure.amount)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="payment-amount">Amount</label>
                <input
                  id="payment-amount"
                  type="number"
                  step="0.01"
                  value={paymentForm.amount}
                  onChange={(event) => setPaymentForm((current) => ({ ...current, amount: event.target.value }))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="payment-mode">Payment mode</label>
                <select
                  id="payment-mode"
                  value={paymentForm.payment_mode}
                  onChange={(event) =>
                    setPaymentForm((current) => ({
                      ...current,
                      payment_mode: event.target.value as PaymentMode,
                    }))
                  }
                >
                  <option value="CASH">CASH</option>
                  <option value="BANK">BANK</option>
                  <option value="UPI">UPI</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="payment-date">Payment date</label>
                <input
                  id="payment-date"
                  type="date"
                  value={paymentForm.payment_date}
                  max={today}
                  onChange={(event) =>
                    setPaymentForm((current) => ({ ...current, payment_date: event.target.value }))
                  }
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button className="accent-button" type="submit" disabled={submitting}>
                Record fee payment
              </button>
              {lastReceipt ? (
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => downloadReceipt(lastReceipt.paymentId, lastReceipt.receiptNumber)}
                >
                  Download latest receipt
                </button>
              ) : null}
            </div>
          </form>

          <div className="detail-stack">
            <div>
              <span className="field-note">Student</span>
              <strong>
                {selectedStudent ? fullName(selectedStudent.first_name, selectedStudent.last_name) : "Select a student"}
              </strong>
            </div>
            <div>
              <span className="field-note">Class</span>
              <strong>{selectedStudent?.class_name || "Not available"}</strong>
            </div>
            <div>
              <span className="field-note">Receipt status</span>
              <strong>{lastReceipt?.receiptNumber || "No new receipt yet"}</strong>
            </div>
          </div>
        </Panel>
      </section>

      <Panel title="Student fee summary" subtitle="Totals and payment history for the currently selected student.">
        {feeSummary ? (
          <>
            <section className="triptych-grid">
              <MetricCard label="Total fee" value={formatCurrency(feeSummary.total_fee)} detail="Configured structure total" tone="sand" />
              <MetricCard label="Paid" value={formatCurrency(feeSummary.total_paid)} detail="Recorded fee payments" tone="mint" />
              <MetricCard label="Pending" value={formatCurrency(feeSummary.pending)} detail="Open student balance" tone="coral" />
            </section>

            <DataTable
              rows={feeSummary.payment_history}
              emptyMessage="No fee payments recorded yet."
              columns={[
                {
                  key: "receipt",
                  label: "Receipt",
                  render: (row) => (
                    <div>
                      <strong>{row.receipt_number}</strong>
                      <div className="field-note">{formatDate(row.payment_date)}</div>
                    </div>
                  ),
                },
                {
                  key: "amount",
                  label: "Amount",
                  render: (row) => formatCurrency(row.amount_paid),
                },
                {
                  key: "mode",
                  label: "Mode",
                  render: (row) => row.payment_mode,
                },
                {
                  key: "action",
                  label: "Receipt",
                  render: (row) => (
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => downloadReceipt(row.id, row.receipt_number)}
                    >
                      Download
                    </button>
                  ),
                },
              ]}
            />
          </>
        ) : (
          <div className="empty-state">Select a student to view fee summary and payment history.</div>
        )}
      </Panel>
    </>
  );
}
