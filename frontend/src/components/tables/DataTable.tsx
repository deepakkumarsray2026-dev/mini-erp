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
      className="overflow-hidden rounded-xl"
      style={{ border: '1px solid #E2E6EA', backgroundColor: '#FFFFFF', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full" style={{ borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#F8F9FB' }}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-widest ${col.className ?? ''}`}
                  style={{ color: '#6B7280', borderBottom: '1px solid #E2E6EA' }}
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
                <td colSpan={columns.length} className="px-4 py-14 text-center text-sm" style={{ color: '#9CA3AF' }}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr
                  key={row.id}
                  className="transition-colors duration-100"
                  style={{ borderTop: idx > 0 ? '1px solid #F3F4F6' : undefined }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#F8FAFF')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-[13px] ${col.className ?? ''}`}
                      style={{ color: '#374151' }}
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
