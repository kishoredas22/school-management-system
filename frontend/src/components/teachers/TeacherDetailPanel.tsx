import { DataTable } from "../DataTable";
import { Panel } from "../Panel";
import { formatCurrency, formatDate } from "../../lib/format";
import type { TeacherDetail, TeacherPaymentRecord } from "../../types";

export function TeacherDetailPanel({
  detailLoading,
  selectedTeacher,
  onDownloadSlip,
  onShareSlip,
}: {
  detailLoading: boolean;
  selectedTeacher: TeacherDetail | null;
  onDownloadSlip: (payment: TeacherPaymentRecord) => void;
  onShareSlip: (payment: TeacherPaymentRecord, channel: "EMAIL" | "WHATSAPP") => void;
}) {
  return (
    <div id="teacher-detail-panel">
      <Panel
        title={selectedTeacher ? `${selectedTeacher.name} detail` : "Teacher detail"}
        subtitle="Open a teacher profile from the list to review assignments, contracts, payment history, and salary slip actions in one place."
      >
      {detailLoading ? (
        <div className="empty-state">Loading teacher detail...</div>
      ) : selectedTeacher ? (
        <div className="field-stack">
          <div className="detail-stack">
            <div>
              <span className="field-note">Email</span>
              <strong>{selectedTeacher.email || "Not provided"}</strong>
            </div>
            <div>
              <span className="field-note">Phone</span>
              <strong>{selectedTeacher.phone || "Not provided"}</strong>
            </div>
            <div>
              <span className="field-note">Salary slip email target</span>
              <strong>{selectedTeacher.email || "Email not available for sharing"}</strong>
            </div>
            <div>
              <span className="field-note">Salary slip WhatsApp target</span>
              <strong>{selectedTeacher.phone || "Phone not available for sharing"}</strong>
            </div>
            <div>
              <span className="field-note">Created</span>
              <strong>{formatDate(selectedTeacher.created_at)}</strong>
            </div>
          </div>

          <Panel title="Assignments" subtitle="Classrooms currently attached to this teacher profile.">
            <div className="list-card">
              {selectedTeacher.assignments?.length ? (
                selectedTeacher.assignments.map((assignment, index) => (
                  <div className="list-row" key={assignment.id || `${assignment.class_id}-${index}`}>
                    <div>
                      <strong>{assignment.class_name || "Class"}</strong>
                      <span className="field-note">{assignment.section_name || "All sections"}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">No classroom assignments linked yet.</div>
              )}
            </div>
          </Panel>

          <Panel title="Contracts" subtitle="All contract records for the selected teacher.">
            <DataTable
              rows={selectedTeacher.contracts}
              emptyMessage="No contracts found for this teacher."
              columns={[
                {
                  key: "year",
                  label: "Academic year",
                  render: (row) => row.academic_year_name,
                },
                {
                  key: "total",
                  label: "Contract total",
                  render: (row) => formatCurrency(row.yearly_contract_amount),
                },
                {
                  key: "monthly",
                  label: "Monthly salary",
                  render: (row) => formatCurrency(row.monthly_salary || 0),
                },
                {
                  key: "created",
                  label: "Created",
                  render: (row) => formatDate(row.created_at),
                },
              ]}
            />
          </Panel>

          <Panel title="Salary slips" subtitle="Download the PDF or trigger a prepared email/WhatsApp share using the saved teacher email or phone on this profile.">
            <DataTable
              rows={selectedTeacher.payments}
              emptyMessage="No salary payments recorded yet."
              columns={[
                {
                  key: "receipt",
                  label: "Receipt",
                  render: (row: TeacherPaymentRecord) => (
                    <div>
                      <strong>{row.receipt_number}</strong>
                      <div className="field-note">{row.academic_year_name}</div>
                    </div>
                  ),
                },
                {
                  key: "paid",
                  label: "Paid amount",
                  render: (row: TeacherPaymentRecord) => formatCurrency(row.amount_paid),
                },
                {
                  key: "date",
                  label: "Payment date",
                  render: (row: TeacherPaymentRecord) => formatDate(row.payment_date),
                },
                {
                  key: "balance",
                  label: "Pending balance",
                  render: (row: TeacherPaymentRecord) => formatCurrency(row.pending_balance),
                },
                {
                  key: "actions",
                  label: "Actions",
                  render: (row: TeacherPaymentRecord) => (
                    <div className="table-action-stack">
                      <button className="ghost-button" type="button" onClick={() => onDownloadSlip(row)}>
                        Download
                      </button>
                      <button
                        className="ghost-button"
                        type="button"
                        disabled={!selectedTeacher.email}
                        onClick={() => onShareSlip(row, "EMAIL")}
                      >
                        Email
                      </button>
                      <button
                        className="ghost-button"
                        type="button"
                        disabled
                        onClick={() => onShareSlip(row, "WHATSAPP")}
                      >
                        WhatsApp later
                      </button>
                      <span className="field-note">
                        Email uses: {selectedTeacher.email || "Not set"} | WhatsApp PDF send needs business sender setup
                      </span>
                    </div>
                  ),
                },
              ]}
            />
          </Panel>
        </div>
      ) : (
        <div className="empty-state">Click a teacher name from the list to open the operational detail view.</div>
      )}
      </Panel>
    </div>
  );
}
