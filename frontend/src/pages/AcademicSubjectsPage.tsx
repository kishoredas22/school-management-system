import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../components/DataTable";
import { Panel } from "../components/Panel";
import { AcademicWorkspace } from "../components/academics/AcademicWorkspace";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { Subject } from "../types";

const emptyForm = {
  name: "",
  code: "",
};

export function AcademicSubjectsPage() {
  const { session, logout } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadSubjects() {
    if (!session) {
      return;
    }

    try {
      setError("");
      const data = await apiRequest<Subject[]>("/academics/subjects", { token: session.accessToken });
      setSubjects(data);
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
    loadSubjects();
  }, [session]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await apiRequest<Subject>("/academics/subjects", {
        method: "POST",
        token: session.accessToken,
        body: form,
      });
      setMessage("Subject created.");
      setForm(emptyForm);
      await loadSubjects();
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

  async function toggleActive(subject: Subject) {
    if (!session) {
      return;
    }

    setError("");
    setMessage("");

    try {
      await apiRequest<Subject>(`/academics/subjects/${subject.id}`, {
        method: "PUT",
        token: session.accessToken,
        body: { is_active: !subject.is_active },
      });
      setMessage(`${subject.name} ${subject.is_active ? "archived" : "activated"}.`);
      await loadSubjects();
    } catch (toggleError) {
      if (isUnauthorizedError(toggleError)) {
        logout();
        return;
      }
      setError(getErrorMessage(toggleError));
    }
  }

  return (
    <AcademicWorkspace
      title="Subjects"
      description="Maintain the subject master so exams, timetable setup, and teacher-subject mapping use one consistent academic catalog."
    >
      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <section className="split-grid">
        <Panel title="Subject register" subtitle="All active and archived subjects available to the academic module.">
          <DataTable<Subject>
            rows={subjects}
            emptyMessage={loading ? "Loading subjects..." : "No subjects created yet."}
            columns={[
              { key: "code", label: "Code", render: (row) => <strong>{row.code}</strong> },
              { key: "name", label: "Subject", render: (row) => row.name },
              {
                key: "status",
                label: "Status",
                render: (row) => (
                  <span className={`status-pill ${row.is_active ? "status-active" : "status-inactive"}`.trim()}>
                    {row.is_active ? "ACTIVE" : "INACTIVE"}
                  </span>
                ),
              },
              {
                key: "actions",
                label: "Actions",
                render: (row) => (
                  <button className="ghost-button" type="button" onClick={() => toggleActive(row)}>
                    {row.is_active ? "Archive" : "Activate"}
                  </button>
                ),
              },
            ]}
          />
        </Panel>

        <Panel title="Create subject" subtitle="Set the name and code once, then reuse it everywhere in academics.">
          <form className="field-stack" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="subject-name">Subject name</label>
              <input
                id="subject-name"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                placeholder="Mathematics"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="subject-code">Subject code</label>
              <input
                id="subject-code"
                value={form.code}
                onChange={(event) => setForm((current) => ({ ...current, code: event.target.value.toUpperCase() }))}
                placeholder="MATH"
                required
              />
            </div>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Saving..." : "Create subject"}
              </button>
            </div>
          </form>
        </Panel>
      </section>
    </AcademicWorkspace>
  );
}
