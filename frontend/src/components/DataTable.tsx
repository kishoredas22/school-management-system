import type { ReactNode } from "react";

interface Column<T> {
  key: string;
  label: string;
  render: (row: T, index: number) => ReactNode;
}

function resolveRowKey<T>(row: T, index: number, fallbackKey: string): string {
  if (typeof row === "object" && row !== null && "id" in row) {
    const value = (row as { id?: unknown }).id;
    if (typeof value === "string" && value) {
      return value;
    }
  }
  return `${index}-${fallbackKey}`;
}

export function DataTable<T>({
  columns,
  rows,
  emptyMessage,
  getRowKey,
}: {
  columns: Column<T>[];
  rows: T[];
  emptyMessage: string;
  getRowKey?: (row: T, index: number) => string;
}) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr key={getRowKey ? getRowKey(row, index) : resolveRowKey(row, index, columns[0]?.key || "row")}>
                {columns.map((column) => (
                  <td key={column.key}>{column.render(row, index)}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>
                <div className="empty-state">{emptyMessage}</div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
