import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import { hasPermission, useAuth } from "../../lib/auth";
import type { PermissionCode, UserRole } from "../../types";
import { PageIntro } from "../PageIntro";

interface AcademicNavItem {
  to: string;
  label: string;
  roles: UserRole[];
  permission: PermissionCode;
}

const navItems: AcademicNavItem[] = [
  { to: "/academics/subjects", label: "Subjects", roles: ["SUPER_ADMIN", "ADMIN"], permission: "SUBJECT_MANAGE" },
  {
    to: "/academics/mappings",
    label: "Teacher-Subject",
    roles: ["SUPER_ADMIN", "ADMIN"],
    permission: "TEACHER_SUBJECT_MANAGE",
  },
  { to: "/academics/exams", label: "Exams", roles: ["SUPER_ADMIN", "ADMIN"], permission: "EXAM_MANAGE" },
  { to: "/academics/marks", label: "Marks", roles: ["SUPER_ADMIN", "ADMIN", "TEACHER"], permission: "MARKS_ENTRY" },
  { to: "/academics/grades", label: "Grade Rules", roles: ["SUPER_ADMIN", "ADMIN"], permission: "GRADE_RULE_MANAGE" },
  { to: "/academics/timetable", label: "Timetable", roles: ["SUPER_ADMIN", "ADMIN"], permission: "TIMETABLE_MANAGE" },
  {
    to: "/academics/report-cards",
    label: "Report Cards",
    roles: ["SUPER_ADMIN", "ADMIN"],
    permission: "REPORT_CARD_VIEW",
  },
];

export function firstAcademicRoute(sessionRole: UserRole, permissions: PermissionCode[]): string {
  const session = {
    role: sessionRole,
    permissions,
    accessToken: "",
    loginMode: "PASSWORD" as const,
    tokenType: "bearer",
    username: "",
  };
  const firstMatch = navItems.find((item) => item.roles.includes(sessionRole) && hasPermission(session, item.permission));
  return firstMatch?.to || "/dashboard";
}

export function AcademicWorkspace({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const { session } = useAuth();
  const location = useLocation();

  const visibleItems = navItems.filter(
    (item) => session && item.roles.includes(session.role) && hasPermission(session, item.permission),
  );

  return (
    <>
      <PageIntro eyebrow="Academic management" title={title} description={description} actions={actions} />

      <nav className="academic-nav" aria-label="Academic sections">
        {visibleItems.map((item) => (
          <Link
            key={item.to}
            className={`academic-nav-link ${location.pathname === item.to ? "is-active" : ""}`.trim()}
            to={item.to}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      {children}
    </>
  );
}
