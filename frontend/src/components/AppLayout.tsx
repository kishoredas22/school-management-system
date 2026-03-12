import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

import { hasPermission, useAuth } from "../lib/auth";
import type { PermissionCode, UserRole } from "../types";
import { SchoolBrand } from "./SchoolBrand";

interface NavItem {
  to: string;
  label: string;
  badge: string;
  roles: UserRole[];
  permission?: PermissionCode;
}

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Overview", badge: "Live", roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "DATA_ENTRY"] },
  { to: "/academics", label: "Academics", badge: "Exam", roles: ["SUPER_ADMIN", "ADMIN"], permission: "REFERENCE_MANAGE" },
  {
    to: "/students",
    label: "Students",
    badge: "Roster",
    roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "DATA_ENTRY"],
    permission: "STUDENT_RECORDS",
  },
  { to: "/teachers", label: "Teachers", badge: "Faculty", roles: ["SUPER_ADMIN", "ADMIN"], permission: "TEACHER_MANAGE" },
  { to: "/fees", label: "Fees", badge: "Finance", roles: ["SUPER_ADMIN", "ADMIN", "DATA_ENTRY"], permission: "FEE_MANAGE" },
  {
    to: "/attendance",
    label: "Attendance",
    badge: "Daily",
    roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "DATA_ENTRY"],
    permission: "ATTENDANCE_STUDENT",
  },
  { to: "/reports", label: "Reports", badge: "Insight", roles: ["SUPER_ADMIN", "ADMIN"], permission: "REPORT_VIEW" },
  { to: "/audit", label: "Audit", badge: "Trace", roles: ["SUPER_ADMIN"], permission: "AUDIT_VIEW" },
  { to: "/users", label: "Access", badge: "Roles", roles: ["SUPER_ADMIN"] },
];

function NavLinkItem({
  to,
  label,
  badge,
  active,
  onClick,
}: {
  to: string;
  label: string;
  badge: string;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <Link className={`nav-link ${active ? "is-active" : ""}`.trim()} to={to} onClick={onClick}>
      <span>{label}</span>
      <small>{badge}</small>
    </Link>
  );
}

export function AppLayout() {
  const { session, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const visibleItems = navItems.filter(
    (item) => session && item.roles.includes(session.role) && (!item.permission || hasPermission(session, item.permission)),
  );
  const currentLabel = visibleItems.find((item) => location.pathname.startsWith(item.to))?.label || "Overview";

  return (
    <div className="app-frame">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <aside className={`side-rail ${menuOpen ? "open" : ""}`.trim()}>
        <div className="brand-block">
          <SchoolBrand
            eyebrow="School Workspace"
            inverted
            stacked
            subtitle="Admissions, academics, attendance, payroll, fee collection, and compliance in one school workspace."
          />
        </div>

        <nav className="nav-stack">
          {visibleItems.map((item) => (
            <NavLinkItem
              key={item.to}
              to={item.to}
              label={item.label}
              badge={item.badge}
              active={location.pathname.startsWith(item.to)}
              onClick={() => setMenuOpen(false)}
            />
          ))}
        </nav>

        <div className="rail-note">
          <span>Signed in</span>
          <strong>{session?.username}</strong>
          <p>{session?.role.replace(/_/g, " ")}</p>
        </div>
      </aside>

      <div className="content-shell">
        <header className="top-bar">
          <div>
            <button className="menu-toggle" type="button" onClick={() => setMenuOpen((value) => !value)}>
              Menu
            </button>
            <p className="eyebrow">Active View</p>
            <h2>{currentLabel}</h2>
          </div>
          <div className="top-bar-actions">
            <div className="role-pill">{session?.role.replace(/_/g, " ")}</div>
            <button className="ghost-button" type="button" onClick={logout}>
              Log out
            </button>
          </div>
        </header>

        <main className="page-shell">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
