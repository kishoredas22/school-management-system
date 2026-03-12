import { Navigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { firstAcademicRoute } from "../components/academics/AcademicWorkspace";

export function AcademicLandingPage() {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={firstAcademicRoute(session.role, session.permissions)} replace />;
}
