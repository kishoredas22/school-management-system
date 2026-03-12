import type { ReactNode } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { hasPermission, useAuth } from "../lib/auth";
import type { PermissionCode, UserRole } from "../types";

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

export function RoleGate({ allowed, children }: { allowed: UserRole[]; children: ReactNode }) {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!allowed.includes(session.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

export function PermissionGate({
  allowed,
  permission,
  children,
}: {
  allowed: UserRole[];
  permission: PermissionCode;
  children: ReactNode;
}) {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!allowed.includes(session.role) || !hasPermission(session, permission)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
