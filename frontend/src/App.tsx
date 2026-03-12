import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { PermissionGate, ProtectedRoute } from "./components/AuthGate";
import { AuthProvider } from "./lib/auth";
import { AcademicsPage } from "./pages/AcademicsPage";
import { AttendancePage } from "./pages/AttendancePage";
import { AuditLogsPage } from "./pages/AuditLogsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FeesPage } from "./pages/FeesPage";
import { LoginPage } from "./pages/LoginPage";
import { ReportsPage } from "./pages/ReportsPage";
import { StudentsPage } from "./pages/StudentsPage";
import { TeacherDetailPage } from "./pages/TeacherDetailPage";
import { TeachersPage } from "./pages/TeachersPage";
import { UsersPage } from "./pages/UsersPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route
                path="/academics"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN"]} permission="REFERENCE_MANAGE">
                    <AcademicsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/students"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN", "TEACHER", "DATA_ENTRY"]} permission="STUDENT_RECORDS">
                    <StudentsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/teachers"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN"]} permission="TEACHER_MANAGE">
                    <TeachersPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/teachers/:teacherId"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN"]} permission="TEACHER_MANAGE">
                    <TeacherDetailPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/fees"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN", "DATA_ENTRY"]} permission="FEE_MANAGE">
                    <FeesPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/attendance"
                element={
                  <PermissionGate
                    allowed={["SUPER_ADMIN", "ADMIN", "TEACHER", "DATA_ENTRY"]}
                    permission="ATTENDANCE_STUDENT"
                  >
                    <AttendancePage />
                  </PermissionGate>
                }
              />
              <Route
                path="/reports"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN", "ADMIN"]} permission="REPORT_VIEW">
                    <ReportsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/audit"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN"]} permission="AUDIT_VIEW">
                    <AuditLogsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/users"
                element={
                  <PermissionGate allowed={["SUPER_ADMIN"]} permission="USER_MANAGE">
                    <UsersPage />
                  </PermissionGate>
                }
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
