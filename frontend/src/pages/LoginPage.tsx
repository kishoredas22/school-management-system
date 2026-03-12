import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { SchoolBrand } from "../components/SchoolBrand";
import { useAuth } from "../lib/auth";
import { getErrorMessage } from "../lib/errors";

type LoginView = "password" | "email";

export function LoginPage() {
  const { isAuthenticated, login, requestEmailLink, consumeEmailLink } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [view, setView] = useState<LoginView>("password");
  const [username, setUsername] = useState("superadmin");
  const [password, setPassword] = useState("password123");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [emailPreviewUrl, setEmailPreviewUrl] = useState("");

  const nextPath = useMemo(
    () => ((location.state as { from?: string } | null)?.from || "/dashboard"),
    [location.state],
  );
  const emailToken = useMemo(() => new URLSearchParams(location.search).get("email_token"), [location.search]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    document.body.classList.add("login-route");
    return () => {
      document.body.classList.remove("login-route");
    };
  }, []);

  useEffect(() => {
    if (!emailToken || isAuthenticated) {
      return;
    }

    const token = emailToken;
    let cancelled = false;

    async function consumeToken() {
      setSubmitting(true);
      setError("");
      setMessage("Signing you in from the email link...");
      try {
        await consumeEmailLink(token);
        if (!cancelled) {
          navigate(nextPath, { replace: true });
        }
      } catch (submitError) {
        if (!cancelled) {
          setError(getErrorMessage(submitError));
          setMessage("");
          setView("email");
        }
      } finally {
        if (!cancelled) {
          setSubmitting(false);
        }
      }
    }

    consumeToken();

    return () => {
      cancelled = true;
    };
  }, [consumeEmailLink, emailToken, isAuthenticated, navigate, nextPath]);

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await login(username, password);
      navigate(nextPath, { replace: true });
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setMessage("");
    setEmailPreviewUrl("");

    try {
      const response = await requestEmailLink(email);
      setMessage(
        response.login_url
          ? "Email-link sign-in is ready. Until email delivery is configured, you can open the preview URL below."
          : "If this email is linked to an active account, a sign-in link has been prepared.",
      );
      setEmailPreviewUrl(response.login_url || "");
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-panel">
        <div className="login-panel-copy">
          <SchoolBrand
            compact
            eyebrow="Welcome to VSK"
            subtitle="Unified operations for admissions, fees, attendance, teacher payroll, reporting, and audit-ready record keeping."
          />
          <div className="login-panel-story">
            <p className="eyebrow">School Workspace</p>
            <h2>Run the full school office from one workspace.</h2>
            <p>
              Admissions, fees, attendance, teacher payroll, reporting, and audit visibility stay in one connected
              system for daily use.
            </p>
          </div>
        </div>

        <section className="login-card login-form-card">
          <p className="eyebrow">Access Portal</p>
          <h1>Sign in</h1>
          <p className="page-copy">
            Use local credentials for backoffice accounts, or request an email login link for email-linked staff.
          </p>

          <div className="segmented login-auth-switch">
            <button className={view === "password" ? "is-active" : ""} type="button" onClick={() => setView("password")}>
              Password
            </button>
            <button className={view === "email" ? "is-active" : ""} type="button" onClick={() => setView("email")}>
              Email link
            </button>
          </div>

          {error ? <div className="message-banner is-error">{error}</div> : null}
          {message ? <div className="message-banner is-success">{message}</div> : null}
          {emailPreviewUrl ? (
            <div className="message-banner">
              <div className="toolbar">
                <a className="ghost-button" href={emailPreviewUrl} target="_blank" rel="noreferrer">
                  Open sign-in link
                </a>
                <span className="field-note">{emailPreviewUrl}</span>
              </div>
            </div>
          ) : null}

          {view === "password" ? (
            <form className="subtle-grid" onSubmit={handlePasswordSubmit}>
              <div className="field">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  name="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                />
              </div>

              <div className="field">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                />
              </div>

              <div className="form-actions">
                <button className="accent-button" type="submit" disabled={submitting}>
                  {submitting ? "Signing in..." : "Enter workspace"}
                </button>
              </div>
            </form>
          ) : (
            <form className="subtle-grid" onSubmit={handleEmailSubmit}>
              <div className="field">
                <label htmlFor="email-login">Linked email</label>
                <input
                  id="email-login"
                  name="email-login"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  placeholder="teacher.user@gmail.com"
                  required
                />
              </div>

              <div className="message-banner">
                Email-linked users do not use local password reset. They sign in only from a one-time email login link.
              </div>

              <div className="form-actions">
                <button className="accent-button" type="submit" disabled={submitting}>
                  {submitting ? "Preparing link..." : "Request email link"}
                </button>
              </div>
            </form>
          )}
        </section>
      </section>
    </div>
  );
}
