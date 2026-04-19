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
    <div
      className="overflow-hidden rounded-xl shadow-sm"
      style={{ border: '1px solid #2a2a2e', backgroundColor: '#1c1c1e' }}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full" style={{ borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#111113' }}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-widest ${col.className ?? ''}`}
                  style={{ color: '#555558', borderBottom: '1px solid #232326' }}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-14 text-center">
                  <Spinner className="mx-auto" />
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-14 text-center text-sm"
                  style={{ color: '#555558' }}
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr
                  key={row.id}
                  className="transition-colors duration-100"
                  style={{ borderTop: idx > 0 ? '1px solid #232326' : undefined }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#222224')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-[13px] ${col.className ?? ''}`}
                      style={{ color: '#c4c0b8' }}
                    >
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
