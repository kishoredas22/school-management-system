import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { TeacherListPanel } from "../components/teachers/TeacherListPanel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest, downloadFile } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { formatCurrency, formatDate } from "../lib/format";
import type {
  AcademicYear,
  ClassRoom,
  PaymentMode,
  Section,
  Teacher,
  TeacherContract,
} from "../types";
import {
  deriveMonthlySalary,
  emptyAssignmentDraft,
  emptyContractForm,
  emptyTeacherForm,
} from "../components/teachers/teacherHelpers";

const emptyPaymentForm = {
  teacher_id: "",
  contract_id: "",
  amount: "",
  payment_mode: "CASH" as PaymentMode,
  payment_date: "",
};

const today = new Date().toISOString().slice(0, 10);

export function TeachersPage() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [contracts, setContracts] = useState<TeacherContract[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [editingTeacherId, setEditingTeacherId] = useState<string | null>(null);
  const [teacherForm, setTeacherForm] = useState(emptyTeacherForm);
  const [assignmentDraft, setAssignmentDraft] = useState(emptyAssignmentDraft);
  const [teacherAssignments, setTeacherAssignments] = useState<typeof emptyAssignmentDraft[]>([]);
  const [contractForm, setContractForm] = useState(emptyContractForm);
  const [contractMonthlyAuto, setContractMonthlyAuto] = useState(true);
  const [paymentForm, setPaymentForm] = useState(emptyPaymentForm);
  const [lastSlip, setLastSlip] = useState<{ paymentId: string; receiptNumber: string } | null>(null);

  async function loadTeacherCollections() {
    if (!session) {
      return;
    }

    setError("");

    try {
      const [teacherList, yearList, classList, sectionList, contractList] = await Promise.all([
        apiRequest<Teacher[]>("/teachers", { token: session.accessToken }),
        apiRequest<AcademicYear[]>("/academic-years", { token: session.accessToken }),
        apiRequest<ClassRoom[]>("/reference/classes", { token: session.accessToken }),
        apiRequest<Section[]>("/reference/sections", { token: session.accessToken }),
        apiRequest<TeacherContract[]>("/teachers/contracts", { token: session.accessToken }),
      ]);

      const activeYear = yearList.find((item) => item.is_active) || yearList[0];
      setTeachers(teacherList);
      setAcademicYears(yearList);
      setClasses(classList);
      setSections(sectionList);
      setContracts(contractList);
      setContractForm((current) => ({
        ...current,
        academic_year_id: current.academic_year_id || activeYear?.id || "",
      }));
      setPaymentForm((current) => ({
        ...current,
        payment_date: current.payment_date || today,
      }));
      setAssignmentDraft((current) => ({
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

  async function loadData() {
    setLoading(true);
    await loadTeacherCollections();
    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, [session]);

  const assignmentSections = sections.filter(
    (section) => !assignmentDraft.class_id || section.class_id === assignmentDraft.class_id,
  );
  const teacherScopedContracts = contracts.filter(
    (item) => !paymentForm.teacher_id || item.teacher_id === paymentForm.teacher_id,
  );

  function resetTeacherForm() {
    setEditingTeacherId(null);
    setTeacherForm(emptyTeacherForm);
    setTeacherAssignments([]);
    setAssignmentDraft((current) => ({
      ...emptyAssignmentDraft,
      academic_year_id: current.academic_year_id,
    }));
  }

  function resetContractForm() {
    setContractMonthlyAuto(true);
    setContractForm((current) => ({
      ...emptyContractForm,
      academic_year_id: current.academic_year_id,
    }));
  }

  function addAssignment() {
    if (!assignmentDraft.class_id) {
      return;
    }
    setTeacherAssignments((current) => [...current, assignmentDraft]);
    setAssignmentDraft((current) => ({ ...current, class_id: "", section_id: "" }));
  }

  function removeAssignment(index: number) {
    setTeacherAssignments((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function startEditing(teacher: Teacher) {
    setEditingTeacherId(teacher.id);
    setTeacherForm({
      name: teacher.name,
      phone: teacher.phone || "",
      email: teacher.email || "",
      is_active: teacher.is_active,
    });
    setTeacherAssignments(
      (teacher.assignments || []).map((assignment) => ({
        class_id: assignment.class_id || "",
        section_id: assignment.section_id || "",
        academic_year_id: assignment.academic_year_id || "",
      })),
    );
  }

  async function handleTeacherSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const payload = {
        name: teacherForm.name,
        phone: teacherForm.phone || null,
        email: teacherForm.email || null,
        is_active: teacherForm.is_active,
        assigned_classes: teacherAssignments.map((item) => ({
          class_id: item.class_id,
          section_id: item.section_id || null,
          academic_year_id: item.academic_year_id || null,
        })),
      };

      if (editingTeacherId) {
        await apiRequest(`/teachers/${editingTeacherId}`, {
          method: "PUT",
          token: session.accessToken,
          body: payload,
        });
        setMessage("Teacher updated successfully.");
      } else {
        await apiRequest("/teachers", {
          method: "POST",
          token: session.accessToken,
          body: payload,
        });
        setMessage("Teacher created successfully.");
      }

      resetTeacherForm();
      await loadTeacherCollections();
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

  async function handleContractSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest("/teachers/contracts", {
        method: "POST",
        token: session.accessToken,
        body: {
          teacher_id: contractForm.teacher_id,
          academic_year_id: contractForm.academic_year_id,
          yearly_contract_amount: contractForm.yearly_contract_amount,
          monthly_salary: contractForm.monthly_salary || null,
        },
      });
      setMessage("Teacher contract created.");
      resetContractForm();
      await loadTeacherCollections();
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
      const response = await apiRequest<{ id: string; receipt_number: string }>("/teachers/payments", {
        method: "POST",
        token: session.accessToken,
        body: {
          teacher_id: paymentForm.teacher_id,
          contract_id: paymentForm.contract_id,
          amount: paymentForm.amount,
          payment_mode: paymentForm.payment_mode,
          payment_date: paymentForm.payment_date,
        },
      });
      setLastSlip({ paymentId: response.id, receiptNumber: response.receipt_number });
      setMessage(`Salary payment recorded. Receipt ${response.receipt_number} is ready.`);
      setPaymentForm((current) => ({
        ...emptyPaymentForm,
        payment_date: current.payment_date,
      }));
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

  async function downloadLastSlip() {
    if (!session || !lastSlip) {
      return;
    }

    try {
      await downloadFile(`/teachers/payments/${lastSlip.paymentId}/slip`, session.accessToken, `${lastSlip.receiptNumber}.pdf`);
    } catch (downloadError) {
      setError(getErrorMessage(downloadError));
    }
  }

  return (
    <>
      <PageIntro
        eyebrow="Faculty and payroll"
        title="Teachers"
        description="Manage teacher profiles, assignment metadata, contracts, and salary payments. Salary slips now show the payment month, attendance-backed worked days, and paid-for-month versus year-to-date totals."
        actions={
          lastSlip ? (
            <button className="accent-button" type="button" onClick={downloadLastSlip}>
              Download latest salary slip
            </button>
          ) : undefined
        }
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="split-grid">
        <TeacherListPanel
          teachers={teachers}
          loading={loading}
          onOpenDetail={(teacherId) => navigate(`/teachers/${teacherId}`)}
          onEdit={startEditing}
        />

        <Panel
          title={editingTeacherId ? "Edit teacher" : "Create teacher"}
          subtitle="Assignments entered here define where a linked teacher account can work inside attendance and other scoped features."
        >
          <form className="field-stack" onSubmit={handleTeacherSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="teacher-name">Name</label>
                <input
                  id="teacher-name"
                  value={teacherForm.name}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, name: event.target.value }))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="teacher-phone">Phone</label>
                <input
                  id="teacher-phone"
                  value={teacherForm.phone}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, phone: event.target.value }))}
                />
              </div>
              <div className="field">
                <label htmlFor="teacher-email">Email</label>
                <input
                  id="teacher-email"
                  type="email"
                  value={teacherForm.email}
                  onChange={(event) => setTeacherForm((current) => ({ ...current, email: event.target.value }))}
                />
              </div>
              <div className="field">
                <label htmlFor="teacher-active">Active</label>
                <select
                  id="teacher-active"
                  value={String(teacherForm.is_active)}
                  onChange={(event) =>
                    setTeacherForm((current) => ({ ...current, is_active: event.target.value === "true" }))
                  }
                >
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <div>
                  <h2>Assignment builder</h2>
                  <p>Use this to define the classes and sections attached to the teacher profile.</p>
                </div>
              </div>

              <div className="form-grid">
                <div className="field">
                  <label htmlFor="assignment-class">Class</label>
                  <select
                    id="assignment-class"
                    value={assignmentDraft.class_id}
                    onChange={(event) =>
                      setAssignmentDraft((current) => ({
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
                  <label htmlFor="assignment-section">Section</label>
                  <select
                    id="assignment-section"
                    value={assignmentDraft.section_id}
                    onChange={(event) =>
                      setAssignmentDraft((current) => ({ ...current, section_id: event.target.value }))
                    }
                  >
                    <option value="">All sections</option>
                    {assignmentSections.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="assignment-year">Academic year</label>
                  <select
                    id="assignment-year"
                    value={assignmentDraft.academic_year_id}
                    onChange={(event) =>
                      setAssignmentDraft((current) => ({ ...current, academic_year_id: event.target.value }))
                    }
                  >
                    <option value="">Any year</option>
                    {academicYears.map((year) => (
                      <option key={year.id} value={year.id}>
                        {year.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="toolbar">
                <button className="soft-button" type="button" onClick={addAssignment}>
                  Add assignment
                </button>
              </div>

              <div className="list-card">
                {teacherAssignments.length ? (
                  teacherAssignments.map((item, index) => (
                    <div className="list-row" key={`${item.class_id}-${item.section_id || "all"}-${index}`}>
                      <div>
                        <strong>{classes.find((row) => row.id === item.class_id)?.name || "Class"}</strong>
                        <span className="field-note">
                          {sections.find((row) => row.id === item.section_id)?.name || "All sections"} |{" "}
                          {academicYears.find((row) => row.id === item.academic_year_id)?.name || "Any year"}
                        </span>
                      </div>
                      <button className="ghost-button" type="button" onClick={() => removeAssignment(index)}>
                        Remove
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">No assignment rows staged yet.</div>
                )}
              </div>
            </div>

            <div className="form-actions">
              <button className="accent-button" type="submit" disabled={submitting}>
                {submitting ? "Saving..." : editingTeacherId ? "Update teacher" : "Create teacher"}
              </button>
              <button className="ghost-button" type="button" onClick={resetTeacherForm}>
                Clear
              </button>
            </div>
          </form>
        </Panel>
      </section>

      <section className="stack-grid">
        <Panel title="Contracts" subtitle="Enter the yearly contract amount and the monthly field fills automatically; change it only if payroll needs an override.">
          <form className="field-stack" onSubmit={handleContractSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="contract-teacher">Teacher</label>
                <select
                  id="contract-teacher"
                  value={contractForm.teacher_id}
                  onChange={(event) => setContractForm((current) => ({ ...current, teacher_id: event.target.value }))}
                  required
                >
                  <option value="">Select teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="contract-year">Academic year</label>
                <select
                  id="contract-year"
                  value={contractForm.academic_year_id}
                  onChange={(event) =>
                    setContractForm((current) => ({ ...current, academic_year_id: event.target.value }))
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
                <label htmlFor="contract-total">Yearly contract amount</label>
                <input
                  id="contract-total"
                  type="number"
                  step="0.01"
                  value={contractForm.yearly_contract_amount}
                  onChange={(event) =>
                    setContractForm((current) => ({
                      ...current,
                      yearly_contract_amount: event.target.value,
                      monthly_salary: contractMonthlyAuto
                        ? deriveMonthlySalary(event.target.value)
                        : current.monthly_salary,
                    }))
                  }
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="contract-monthly">Monthly salary</label>
                <input
                  id="contract-monthly"
                  type="number"
                  step="0.01"
                  value={contractForm.monthly_salary}
                  onChange={(event) => {
                    const value = event.target.value;
                    setContractMonthlyAuto(value === "");
                    setContractForm((current) => ({
                      ...current,
                      monthly_salary: value === "" ? deriveMonthlySalary(current.yearly_contract_amount) : value,
                    }));
                  }}
                />
                <span className="field-note">
                  {contractMonthlyAuto ? "Auto-filled from the yearly amount." : "Manual override enabled."}
                </span>
              </div>
            </div>

            <div className="form-actions">
              <button className="soft-button" type="submit" disabled={submitting}>
                Create contract
              </button>
            </div>
          </form>

          <DataTable
                rows={contracts}
                emptyMessage="No contracts created yet."
                columns={[
                  {
                    key: "teacher",
                    label: "Teacher",
                    render: (row: TeacherContract) => (
                      <div>
                        <strong>{row.teacher_name}</strong>
                        <div className="field-note">{row.academic_year_name}</div>
                      </div>
                    ),
                  },
                  {
                    key: "amount",
                    label: "Contract total",
                    render: (row: TeacherContract) => formatCurrency(row.yearly_contract_amount),
                  },
                  {
                    key: "monthly",
                    label: "Monthly",
                    render: (row: TeacherContract) => formatCurrency(row.monthly_salary || 0),
                  },
                  {
                    key: "created",
                    label: "Created",
                    render: (row: TeacherContract) => formatDate(row.created_at),
                  },
                ]}
              />
        </Panel>

        <Panel title="Salary payment" subtitle="Pick a contract, record a payment, and download the latest salary slip with month summary and attendance-backed work days immediately afterward.">
          <form className="field-stack" onSubmit={handlePaymentSubmit}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="payment-teacher">Teacher</label>
                <select
                  id="payment-teacher"
                  value={paymentForm.teacher_id}
                  onChange={(event) =>
                    setPaymentForm((current) => ({
                      ...current,
                      teacher_id: event.target.value,
                      contract_id: "",
                    }))
                  }
                  required
                >
                  <option value="">Select teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="payment-contract">Contract</label>
                <select
                  id="payment-contract"
                  value={paymentForm.contract_id}
                  onChange={(event) => setPaymentForm((current) => ({ ...current, contract_id: event.target.value }))}
                  required
                >
                  <option value="">Select contract</option>
                  {teacherScopedContracts.map((contract) => (
                    <option key={contract.id} value={contract.id}>
                      {contract.teacher_name} | {contract.academic_year_name} | {formatCurrency(contract.monthly_salary || 0)}
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
                  {["CASH", "BANK", "UPI"].map((mode) => (
                    <option key={mode} value={mode}>
                      {mode}
                    </option>
                  ))}
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
                Record salary payment
              </button>
            </div>
          </form>

          {lastSlip ? (
            <div className="message-banner">
              Latest slip ready: <strong>{lastSlip.receiptNumber}</strong>
            </div>
          ) : (
            <div className="empty-state">Salary slip download appears here after a payment is recorded.</div>
          )}
        </Panel>
      </section>
    </>
  );
}
