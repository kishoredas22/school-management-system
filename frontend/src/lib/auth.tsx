import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

import { ApiError, apiRequest } from "./api";
import type { EmailLinkPreview, LoginResponse, PermissionCode, Session } from "../types";

interface AuthContextValue {
  session: Session | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  requestEmailLink: (email: string) => Promise<EmailLinkPreview>;
  consumeEmailLink: (token: string) => Promise<void>;
  logout: () => void;
}

const storageKey = "school-management-session";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredSession(): Session | null {
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<Session>;
    if (!parsed.accessToken || !parsed.role || !parsed.username || !Array.isArray(parsed.permissions)) {
      window.localStorage.removeItem(storageKey);
      return null;
    }
    return {
      accessToken: parsed.accessToken,
      tokenType: parsed.tokenType || "bearer",
      role: parsed.role,
      username: parsed.username,
      loginMode: parsed.loginMode || "PASSWORD",
      permissions: parsed.permissions as PermissionCode[],
    };
  } catch {
    window.localStorage.removeItem(storageKey);
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(() => readStoredSession());

  function persistSession(response: LoginResponse) {
    const nextSession: Session = {
      accessToken: response.access_token,
      tokenType: response.token_type,
      role: response.role,
      username: response.username,
      loginMode: response.login_mode,
      permissions: response.permissions,
    };
    window.localStorage.setItem(storageKey, JSON.stringify(nextSession));
    setSession(nextSession);
  }

  async function login(username: string, password: string) {
    const response = await apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    persistSession(response);
  }

  async function requestEmailLink(email: string) {
    return apiRequest<EmailLinkPreview>("/auth/email-link/request", {
      method: "POST",
      body: { email },
    });
  }

  async function consumeEmailLink(token: string) {
    const response = await apiRequest<LoginResponse>("/auth/email-link/consume", {
      method: "POST",
      body: { token },
    });
    persistSession(response);
  }

  function logout() {
    window.localStorage.removeItem(storageKey);
    setSession(null);
  }

  return (
    <AuthContext.Provider
      value={{
        session,
        isAuthenticated: Boolean(session?.accessToken),
        login,
        requestEmailLink,
        consumeEmailLink,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

export function hasPermission(session: Session | null, permission: PermissionCode): boolean {
  if (!session) {
    return false;
  }
  if (session.role === "SUPER_ADMIN") {
    return true;
  }
  return session.permissions.includes(permission);
}
