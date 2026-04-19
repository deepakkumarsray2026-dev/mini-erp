import { Spinner } from '../common/Spinner'
import { Pagination } from '../common/Pagination'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => React.ReactNode
  className?: string
}

interface Props<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  page?: number
  pages?: number
  total?: number
  onPage?: (p: number) => void
  emptyMessage?: string
}

export function DataTable<T extends { id: string }>({
  columns,
  data,
  loading,
  page,
  pages,
  total,
  onPage,
  emptyMessage = 'No records found.',
}: Props<T>) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-card">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-100">
          <thead>
            <tr className="bg-gray-50/70">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-widest text-gray-400 ${col.className ?? ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-14 text-center">
                  <Spinner className="mx-auto" />
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-14 text-center text-sm text-gray-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr key={row.id} className="hover:bg-blue-50/30 transition-colors duration-100">
                  {columns.map((col) => (
                    <td key={col.key} className={`px-4 py-3 text-[13px] text-gray-700 ${col.className ?? ''}`}>
                      {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {page && pages && total && onPage && (
        <Pagination page={page} pages={pages} total={total} onPage={onPage} />
      )}
    </div>
  )
}
