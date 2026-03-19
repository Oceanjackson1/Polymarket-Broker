import type { ReactNode } from "react";
import { clsx } from "clsx";

export interface Column<T> {
  key: string;
  header: string;
  /** Alignment for both header and cells. Default: "left" */
  align?: "left" | "center" | "right";
  /** Render a custom cell. Receives the row and its index. */
  render?: (row: T, index: number) => ReactNode;
  /** Access a raw string/number value when no custom render is needed */
  accessor?: (row: T) => string | number | null | undefined;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  /** Key field for React reconciliation — defaults to using array index */
  keyField?: keyof T;
  className?: string;
  /** Show a centered message when data is empty */
  emptyMessage?: string;
}

const alignClass = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
};

export function DataTable<T>({
  columns,
  data,
  keyField,
  className,
  emptyMessage = "No data",
}: DataTableProps<T>) {
  return (
    <div className={clsx("overflow-x-auto", className)}>
      <table className="w-full border-collapse font-mono text-sm">
        <thead>
          <tr className="border-b border-border-subtle">
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx(
                  "px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted",
                  alignClass[col.align ?? "left"]
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-8 text-center text-xs text-text-muted"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => {
              const key = keyField
                ? String(row[keyField])
                : String(rowIndex);
              return (
                <tr
                  key={key}
                  className={clsx(
                    "border-b border-border-subtle transition-colors hover:bg-bg-hover",
                    rowIndex % 2 === 0 ? "bg-bg-card" : "bg-bg-base"
                  )}
                >
                  {columns.map((col) => {
                    const content = col.render
                      ? col.render(row, rowIndex)
                      : col.accessor
                        ? (col.accessor(row) ?? "—")
                        : "—";
                    return (
                      <td
                        key={col.key}
                        className={clsx(
                          "px-3 py-2 text-text-secondary",
                          alignClass[col.align ?? "left"]
                        )}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
