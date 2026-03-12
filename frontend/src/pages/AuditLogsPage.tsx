import { useEffect, useState } from "react";

import { DataTable } from "../components/DataTable";
import { MetricCard } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { Panel } from "../components/Panel";
import { downloadFile, apiRequest } from "../lib/api";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { getErrorMessage } from "../lib/errors";
import { formatDate } from "../lib/format";
import type { AuditLog, AuditSummary, Paginated } from "../types";

const emptyPage: Paginated<AuditLog> = {
  page: 1,
  size: 20,
  total_records: 0,
  total_pages: 0,
  data: [],
};

function previewPayload(payload: Record<string, unknown> | null): string {
  if (!payload) {
    return "No payload";
  }
  const serialized = JSON.stringify(payload);
  return serialized.length > 120 ? `${serialized.slice(0, 117)}...` : serialized;
}

export function AuditLogsPage() {
  const { session, logout } = useAuth();
  const [entityFilter, setEntityFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [reviewStatusFilter, setReviewStatusFilter] = useState("");
  const [requiresReviewOnly, setRequiresReviewOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [logs, setLogs] = useState<Paginated<AuditLog>>(emptyPage);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadAuditData(pageOverride?: number) {
    if (!session) {
      return;
    }

    const page = pageOverride ?? logs.page;
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        page: String(page),
        size: String(logs.size),
      });
      if (entityFilter) {
        params.set("entity", entityFilter);
      }
      if (actionFilter) {
        params.set("action", actionFilter);
      }
      if (actorFilter) {
        params.set("actor", actorFilter);
      }
      if (reviewStatusFilter) {
        params.set("review_status", reviewStatusFilter);
      }
      if (requiresReviewOnly) {
        params.set("requires_review", "true");
      }
      if (dateFrom) {
        params.set("date_from", dateFrom);
      }
      if (dateTo) {
        params.set("date_to", dateTo);
      }

      const [pageData, summaryData] = await Promise.all([
        apiRequest<Paginated<AuditLog>>(`/audit-logs?${params.toString()}`, {
          token: session.accessToken,
        }),
        apiRequest<AuditSummary>("/audit-logs/summary", {
          token: session.accessToken,
        }),
      ]);
      setLogs(pageData);
      setSummary(summaryData);
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

  useEffect(() => {
    if (!session) {
      return;
    }
    loadAuditData(1);
  }, [actionFilter, actorFilter, dateFrom, dateTo, entityFilter, logout, requiresReviewOnly, reviewStatusFilter, session]);

  async function handleReview(auditLogId: string, status: "APPROVED" | "REJECTED") {
    if (!session) {
      return;
    }

    setSubmittingId(auditLogId);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/audit-logs/${auditLogId}/review`, {
        method: "POST",
        token: session.accessToken,
        body: {
          status,
          review_note: reviewNotes[auditLogId] || null,
        },
      });
      setMessage(`Audit event ${status === "APPROVED" ? "approved" : "rejected"}.`);
      setReviewNotes((current) => ({ ...current, [auditLogId]: "" }));
      await loadAuditData();
    } catch (submitError) {
      if (isUnauthorizedError(submitError)) {
        logout();
        return;
      }
      setError(getErrorMessage(submitError));
    } finally {
      setSubmittingId("");
    }
  }

  async function handleExport() {
    if (!session) {
      return;
    }

    setError("");
    setMessage("");
    try {
      const params = new URLSearchParams();
      if (entityFilter) {
        params.set("entity", entityFilter);
      }
      if (actionFilter) {
        params.set("action", actionFilter);
      }
      if (actorFilter) {
        params.set("actor", actorFilter);
      }
      if (reviewStatusFilter) {
        params.set("review_status", reviewStatusFilter);
      }
      if (requiresReviewOnly) {
        params.set("requires_review", "true");
      }
      if (dateFrom) {
        params.set("date_from", dateFrom);
      }
      if (dateTo) {
        params.set("date_to", dateTo);
      }
      const suffix = params.toString() ? `?${params.toString()}` : "";
      await downloadFile(`/audit-logs/export${suffix}`, session.accessToken, "audit-log-export.csv");
      setMessage("Audit export downloaded.");
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
        eyebrow="Traceability"
        title="Audit logs"
        description="Filter sensitive events by entity, action, actor, date, and review state. Pending governance reviews can be approved or rejected directly from this screen."
        actions={
          <button className="ghost-button" type="button" onClick={handleExport}>
            Export CSV
          </button>
        }
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="metric-grid">
        <MetricCard
          label="Audit events"
          value={loading ? "..." : String(summary?.total_logs ?? 0)}
          detail="Total immutable events stored"
          tone="sand"
        />
        <MetricCard
          label="Need review"
          value={loading ? "..." : String(summary?.review_required ?? 0)}
          detail="Events flagged for governance review"
          tone="mint"
        />
        <MetricCard
          label="Pending approvals"
          value={loading ? "..." : String(summary?.pending_reviews ?? 0)}
          detail="Awaiting Super Admin decision"
          tone="coral"
        />
        <MetricCard
          label="Reviewed"
          value={loading ? "..." : String((summary?.approved_reviews ?? 0) + (summary?.rejected_reviews ?? 0))}
          detail={`${summary?.approved_reviews ?? 0} approved / ${summary?.rejected_reviews ?? 0} rejected`}
          tone="ink"
        />
      </section>

      <Panel title="Audit feed" subtitle="Super Admin access only.">
        <div className="form-grid">
          <div className="field">
            <label htmlFor="audit-entity">Entity</label>
            <input
              id="audit-entity"
              value={entityFilter}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setEntityFilter(event.target.value);
              }}
              placeholder="USER, STUDENT, FEE_PAYMENT"
            />
          </div>
          <div className="field">
            <label htmlFor="audit-action">Action</label>
            <input
              id="audit-action"
              value={actionFilter}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setActionFilter(event.target.value);
              }}
              placeholder="CREATE, UPDATE, STATUS_CHANGE"
            />
          </div>
          <div className="field">
            <label htmlFor="audit-actor">Actor</label>
            <input
              id="audit-actor"
              value={actorFilter}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setActorFilter(event.target.value);
              }}
              placeholder="Username or actor id"
            />
          </div>
          <div className="field">
            <label htmlFor="audit-review-status">Review status</label>
            <select
              id="audit-review-status"
              value={reviewStatusFilter}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setReviewStatusFilter(event.target.value);
              }}
            >
              <option value="">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="NOT_REQUIRED">Not required</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="audit-date-from">Date from</label>
            <input
              id="audit-date-from"
              type="date"
              value={dateFrom}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setDateFrom(event.target.value);
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="audit-date-to">Date to</label>
            <input
              id="audit-date-to"
              type="date"
              value={dateTo}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setDateTo(event.target.value);
              }}
            />
          </div>
        </div>

        <div className="toolbar">
          <label className="inline-check">
            <input
              type="checkbox"
              checked={requiresReviewOnly}
              onChange={(event) => {
                setLogs((current) => ({ ...current, page: 1 }));
                setRequiresReviewOnly(event.target.checked);
              }}
            />
            <span>Only events requiring review</span>
          </label>
          <span className="field-note">{loading ? "Loading..." : `${logs.total_records} audit records`}</span>
        </div>

        <DataTable
          rows={logs.data}
          emptyMessage="No audit events match the current filter."
          columns={[
            {
              key: "entity",
              label: "Entity",
              render: (row) => (
                <div>
                  <strong>{row.entity_name}</strong>
                  <div className="field-note">{row.entity_id || "No entity id"}</div>
                </div>
              ),
            },
            {
              key: "action",
              label: "Action",
              render: (row) => (
                <div>
                  <strong>{row.action}</strong>
                  <div className={`status-pill ${row.requires_review ? "status-pending" : ""}`}>
                    {row.review_status.replace(/_/g, " ")}
                  </div>
                </div>
              ),
            },
            {
              key: "actor",
              label: "Actor",
              render: (row) => (
                <div>
                  <div>{row.performed_by_username || row.performed_by || "System"}</div>
                  <div className="field-note">
                    {row.reviewed_by_username
                      ? `Reviewed by ${row.reviewed_by_username}`
                      : row.review_status === "PENDING"
                        ? "Awaiting review"
                        : "No review yet"}
                  </div>
                </div>
              ),
            },
            {
              key: "when",
              label: "Performed",
              render: (row) => (
                <div>
                  <div>{formatDate(row.performed_at)}</div>
                  {row.reviewed_at ? <div className="field-note">Reviewed {formatDate(row.reviewed_at)}</div> : null}
                </div>
              ),
            },
            {
              key: "delta",
              label: "Change preview",
              render: (row) => (
                <div>
                  <div className="field-note">New: {previewPayload(row.new_value)}</div>
                  <div className="field-note">Old: {previewPayload(row.old_value)}</div>
                  {row.review_note ? <div className="field-note">Review note: {row.review_note}</div> : null}
                </div>
              ),
            },
            {
              key: "review",
              label: "Governance",
              render: (row) =>
                row.review_status === "PENDING" ? (
                  <div className="table-action-stack">
                    <input
                      className="table-note-input"
                      value={reviewNotes[row.id] || ""}
                      onChange={(event) =>
                        setReviewNotes((current) => ({ ...current, [row.id]: event.target.value }))
                      }
                      placeholder="Optional review note"
                    />
                    <div className="toolbar">
                      <button
                        className="ghost-button"
                        type="button"
                        disabled={submittingId === row.id}
                        onClick={() => handleReview(row.id, "APPROVED")}
                      >
                        Approve
                      </button>
                      <button
                        className="soft-button"
                        type="button"
                        disabled={submittingId === row.id}
                        onClick={() => handleReview(row.id, "REJECTED")}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="field-note">
                    {row.review_status === "NOT_REQUIRED" ? "No review required" : row.review_status.replace(/_/g, " ")}
                  </div>
                ),
            },
          ]}
        />

        <div className="toolbar">
          <button
            className="ghost-button"
            type="button"
            disabled={logs.page <= 1}
            onClick={() => {
              const nextPage = logs.page - 1;
              setLogs((current) => ({ ...current, page: nextPage }));
              loadAuditData(nextPage);
            }}
          >
            Previous
          </button>
          <span className="field-note">
            Page {logs.page} of {Math.max(logs.total_pages, 1)}
          </span>
          <button
            className="ghost-button"
            type="button"
            disabled={logs.page >= Math.max(logs.total_pages, 1)}
            onClick={() => {
              const nextPage = logs.page + 1;
              setLogs((current) => ({ ...current, page: nextPage }));
              loadAuditData(nextPage);
            }}
          >
            Next
          </button>
        </div>
      </Panel>
    </>
  );
}
