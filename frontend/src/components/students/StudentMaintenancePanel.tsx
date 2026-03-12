import type { FormEvent } from "react";

import { Panel } from "../Panel";
import { fullName } from "../../lib/format";
import type { AcademicYear, ClassRoom, PromotionAction, Section, StudentStatus } from "../../types";

interface StudentFormValue {
  student_id: string;
  first_name: string;
  last_name: string;
  dob: string;
  guardian_name: string;
  guardian_phone: string;
  class_id: string;
  section_id: string;
  academic_year_id: string;
}

export function StudentMaintenancePanel({
  academicYears,
  canManageStatus,
  canManageStudents,
  classes,
  editingStudentId,
  onResetStudentForm,
  onSetStatusStudentSearch,
  onStatusFormChange,
  onStatusSubmit,
  onStudentFormChange,
  onStudentSubmit,
  statusForm,
  statusStudentOptions,
  statusStudentSearch,
  studentForm,
  submitting,
  visibleSections,
}: {
  academicYears: AcademicYear[];
  canManageStatus: boolean;
  canManageStudents: boolean;
  classes: ClassRoom[];
  editingStudentId: string | null;
  onResetStudentForm: () => void;
  onSetStatusStudentSearch: (value: string) => void;
  onStatusFormChange: (updater: (current: { studentId: string; status: StudentStatus }) => { studentId: string; status: StudentStatus }) => void;
  onStatusSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onStudentFormChange: (updater: (current: StudentFormValue) => StudentFormValue) => void;
  onStudentSubmit: (event: FormEvent<HTMLFormElement>) => void;
  statusForm: { studentId: string; status: StudentStatus };
  statusStudentOptions: Array<{ id: string; first_name: string; last_name: string | null; student_id: string | null }>;
  statusStudentSearch: string;
  studentForm: StudentFormValue;
  submitting: boolean;
  visibleSections: Section[];
}) {
  return (
    <Panel title={editingStudentId ? "Edit student" : "Register student"} subtitle={canManageStudents ? "Create or revise a student master record." : "Your role can review records only."}>
      {canManageStudents ? (
        <form className="field-stack" onSubmit={onStudentSubmit}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="student-id">Student code</label>
              <input id="student-id" value={studentForm.student_id} onChange={(event) => onStudentFormChange((current) => ({ ...current, student_id: event.target.value }))} placeholder="Leave blank for auto-generation" />
            </div>
            <div className="field">
              <label htmlFor="dob">Date of birth</label>
              <input id="dob" type="date" value={studentForm.dob} onChange={(event) => onStudentFormChange((current) => ({ ...current, dob: event.target.value }))} required />
            </div>
            <div className="field">
              <label htmlFor="first-name">First name</label>
              <input id="first-name" value={studentForm.first_name} onChange={(event) => onStudentFormChange((current) => ({ ...current, first_name: event.target.value }))} required />
            </div>
            <div className="field">
              <label htmlFor="last-name">Last name</label>
              <input id="last-name" value={studentForm.last_name} onChange={(event) => onStudentFormChange((current) => ({ ...current, last_name: event.target.value }))} />
            </div>
            <div className="field">
              <label htmlFor="guardian-name">Guardian name</label>
              <input id="guardian-name" value={studentForm.guardian_name} onChange={(event) => onStudentFormChange((current) => ({ ...current, guardian_name: event.target.value }))} />
            </div>
            <div className="field">
              <label htmlFor="guardian-phone">Guardian phone</label>
              <input id="guardian-phone" value={studentForm.guardian_phone} onChange={(event) => onStudentFormChange((current) => ({ ...current, guardian_phone: event.target.value }))} />
            </div>
            <div className="field">
              <label htmlFor="student-year">Academic year</label>
              <select id="student-year" value={studentForm.academic_year_id} onChange={(event) => onStudentFormChange((current) => ({ ...current, academic_year_id: event.target.value }))} required>
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
                onChange={(event) => onStudentFormChange((current) => ({ ...current, class_id: event.target.value, section_id: "" }))}
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
              <select id="student-section" value={studentForm.section_id} onChange={(event) => onStudentFormChange((current) => ({ ...current, section_id: event.target.value }))} required>
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
            <button className="ghost-button" type="button" onClick={onResetStudentForm}>
              Clear
            </button>
          </div>
        </form>
      ) : (
        <div className="empty-state">Teachers can review the roster here, but student record changes remain disabled.</div>
      )}

      {canManageStatus ? (
        <form className="field-stack" onSubmit={onStatusSubmit}>
          <div className="panel-head">
            <div>
              <h2>Student status</h2>
              <p>Administrative status transitions are handled separately from the edit form.</p>
            </div>
          </div>
          <div className="form-grid">
            <div className="field field-span-2">
              <label htmlFor="status-search">Search student</label>
              <input id="status-search" value={statusStudentSearch} onChange={(event) => onSetStatusStudentSearch(event.target.value)} placeholder="Search by student name or code" />
            </div>
            <div className="field">
              <label htmlFor="status-student">Student</label>
              <select id="status-student" value={statusForm.studentId} onChange={(event) => onStatusFormChange((current) => ({ ...current, studentId: event.target.value }))}>
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
              <select id="status-value" value={statusForm.status} onChange={(event) => onStatusFormChange((current) => ({ ...current, status: event.target.value as StudentStatus }))}>
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
  );
}

export function StudentPromotionPanel({
  academicYears,
  onPromotionFormChange,
  onSubmit,
  promotionForm,
  selectedStudents,
  submitting,
}: {
  academicYears: AcademicYear[];
  onPromotionFormChange: (updater: (current: { academic_year_from: string; academic_year_to: string; action: PromotionAction }) => { academic_year_from: string; academic_year_to: string; action: PromotionAction }) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  promotionForm: { academic_year_from: string; academic_year_to: string; action: PromotionAction };
  selectedStudents: string[];
  submitting: boolean;
}) {
  return (
    <Panel title="Promotion workflow" subtitle="Apply year transition rules to selected students or the supplied year pair.">
      <form className="field-stack" onSubmit={onSubmit}>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="promote-from">From year</label>
            <select id="promote-from" value={promotionForm.academic_year_from} onChange={(event) => onPromotionFormChange((current) => ({ ...current, academic_year_from: event.target.value }))}>
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
            <select id="promote-to" value={promotionForm.academic_year_to} onChange={(event) => onPromotionFormChange((current) => ({ ...current, academic_year_to: event.target.value }))}>
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
            <select id="promotion-action" value={promotionForm.action} onChange={(event) => onPromotionFormChange((current) => ({ ...current, action: event.target.value as PromotionAction }))}>
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
  );
}
