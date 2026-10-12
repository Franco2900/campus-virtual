import EmptyState from "./EmptyState.jsx";

export default function DataTable({
  columns,
  rows,
  rowKey = (row) => row.id,
  rowTestId,
  testId,
  empty = "No hay datos para mostrar.",
  emptyIcon = "bi-inbox",
}) {
  return (
    <div className="table-responsive">
      <table className="table campus-table align-middle mb-0" data-testid={testId}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.className} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} data-testid={rowTestId ? rowTestId(row) : undefined}>
              {columns.map((column) => (
                <td key={column.key} className={column.className}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="p-0">
                <EmptyState icon={emptyIcon}>{empty}</EmptyState>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
