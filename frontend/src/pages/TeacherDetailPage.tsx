import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { PageIntro } from "../components/PageIntro";
import { TeacherDetailPanel } from "../components/teachers/TeacherDetailPanel";
import { useAuth, isUnauthorizedError } from "../lib/auth";
import { apiRequest, downloadFile } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { SalarySlipSharePreview, TeacherDetail, TeacherPaymentRecord } from "../types";

export function TeacherDetailPage() {
  const { teacherId } = useParams();
  const navigate = useNavigate();
  const { session, logout } = useAuth();
  const [detailLoading, setDetailLoading] = useState(true);
  const [selectedTeacher, setSelectedTeacher] = useState<TeacherDetail | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!session || !teacherId) {
      return;
    }

    let isMounted = true;
    const token = session.accessToken;

    async function loadTeacherDetail() {
      setDetailLoading(true);
      setError("");
      try {
        const detail = await apiRequest<TeacherDetail>(`/teachers/${teacherId}`, { token });
        if (isMounted) {
          setSelectedTeacher(detail);
        }
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
          setDetailLoading(false);
        }
      }
    }

    loadTeacherDetail();

    return () => {
      isMounted = false;
    };
  }, [logout, session, teacherId]);

  async function downloadSlip(payment: TeacherPaymentRecord) {
    if (!session) {
      return;
    }

    try {
      await downloadFile(`/teachers/payments/${payment.id}/slip`, session.accessToken, `${payment.receipt_number}.pdf`);
    } catch (downloadError) {
      setError(getErrorMessage(downloadError));
    }
  }

  async function shareSlip(payment: TeacherPaymentRecord, channel: "EMAIL" | "WHATSAPP") {
    if (!session) {
      return;
    }

    try {
      const preview = await apiRequest<SalarySlipSharePreview>(`/teachers/payments/${payment.id}/share`, {
        method: "POST",
        token: session.accessToken,
        body: { channel },
      });
      if (preview.launch_url) {
        window.open(preview.launch_url, "_blank", "noopener,noreferrer");
      }
      setMessage(
        channel === "EMAIL"
          ? `Salary slip emailed to ${preview.destination} from ${preview.sender_email || "the configured sender email"}.`
          : `${channel} share prepared for ${preview.destination}.`,
      );
    } catch (shareError) {
      if (isUnauthorizedError(shareError)) {
        logout();
        return;
      }
      setError(getErrorMessage(shareError));
    }
  }

  if (!teacherId) {
    return null;
  }

  return (
    <>
      <PageIntro
        eyebrow="Faculty and payroll"
        title={selectedTeacher ? selectedTeacher.name : "Teacher detail"}
        description="Teacher profile, assignment scope, contract history, and salary slip actions now live on a dedicated detail page."
        actions={
          <button className="ghost-button" type="button" onClick={() => navigate("/teachers")}>
            Back to teachers
          </button>
        }
      />

      {error ? <div className="message-banner is-error">{error}</div> : null}
      {message ? <div className="message-banner is-success">{message}</div> : null}

      <TeacherDetailPanel
        detailLoading={detailLoading}
        selectedTeacher={selectedTeacher}
        onDownloadSlip={downloadSlip}
        onShareSlip={shareSlip}
      />
    </>
  );
}
