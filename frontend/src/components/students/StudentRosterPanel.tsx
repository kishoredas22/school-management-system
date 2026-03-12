import { DataTable } from "../DataTable";
import { Panel } from "../Panel";
import { buildStudentColumns } from "./studentHelpers";
import type { AcademicYear, ClassRoom, Paginated, Section, StudentRecord } from "../../types";

interface Filters {
  yearId: string;
  classId: string;
  sectionId: string;
  status: string;
  includeInactive: boolean;
  page: number;
  q: string;
}

interface StudentRosterPanelProps {
  academicYears: AcademicYear[];
  classes: ClassRoom[];
  columns: ReturnType<typeof buildStudentColumns>;
  filteredSections: Section[];
  filters: Filters;
  loading: boolean;
  searchInput: string;
  students: Paginated<StudentRecord>;
  onFiltersChange: (updater: (current: Filters) => Filters) => void;
  onSearchInputChange: (value: string) => void;
}

export function StudentRosterPanel({
  academicYears,
  classes,
  columns,
  filteredSections,
  filters,
  loading,
  searchInput,
  students,
  onFiltersChange,
  onSearchInputChange,
}: StudentRosterPanelProps) {
  return (
    <Panel title="Roster browser" subtitle="Live backend list with year, class, section, status, and student search filters.">
      <div className="form-grid">
        <div className="field">
          <label htmlFor="filter-year">Academic year</label>
          <select id="filter-year" value={filters.yearId} onChange={(event) => onFiltersChange((current) => ({ ...current, yearId: event.target.value, page: 1 }))}>
            <option value="">Select year</option>
            {academicYears.map((year) => (
              <option key={year.id} value={year.id}>
                {year.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="filter-class">Class</label>
          <select
            id="filter-class"
            value={filters.classId}
            onChange={(event) =>
              onFiltersChange((current) => ({
                ...current,
                classId: event.target.value,
                sectionId: "",
                page: 1,
              }))
            }
          >
            <option value="">All classes</option>
            {classes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="filter-section">Section</label>
          <select id="filter-section" value={filters.sectionId} onChange={(event) => onFiltersChange((current) => ({ ...current, sectionId: event.target.value }))}>
            <option value="">All sections</option>
            {filteredSections.map((section) => (
              <option key={section.id} value={section.id}>
                {section.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="filter-status">Status</label>
          <select id="filter-status" value={filters.status} onChange={(event) => onFiltersChange((current) => ({ ...current, status: event.target.value, page: 1 }))}>
            <option value="">All statuses</option>
            {["ACTIVE", "PASSED_OUT", "TOOK_TC", "INACTIVE"].map((status) => (
              <option key={status} value={status}>
                {status.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        <div className="field field-span-2">
          <label htmlFor="filter-search">Search student</label>
          <input id="filter-search" value={searchInput} onChange={(event) => onSearchInputChange(event.target.value)} placeholder="Search by student name or code" />
        </div>
      </div>

      <div className="toolbar">
        <label className="check-item">
          <input
            type="checkbox"
            checked={filters.includeInactive}
            onChange={(event) => onFiltersChange((current) => ({ ...current, includeInactive: event.target.checked, page: 1 }))}
          />
          Include inactive students
        </label>
        <span className="field-note">{loading ? "Loading..." : `${students.total_records} total records | ${students.data.length} shown on this page`}</span>
      </div>

      <DataTable rows={students.data} emptyMessage="No students match the current filter." columns={columns} />

      <div className="toolbar">
        <button className="ghost-button" type="button" disabled={filters.page <= 1} onClick={() => onFiltersChange((current) => ({ ...current, page: current.page - 1 }))}>
          Previous
        </button>
        <span className="field-note">
          Page {students.page} of {Math.max(students.total_pages, 1)}
        </span>
        <button
          className="ghost-button"
          type="button"
          disabled={students.page >= Math.max(students.total_pages, 1)}
          onClick={() => onFiltersChange((current) => ({ ...current, page: current.page + 1 }))}
        >
          Next
        </button>
      </div>
    </Panel>
  );
}
