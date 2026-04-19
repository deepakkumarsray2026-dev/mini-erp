import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null

  const btnBase: React.CSSProperties = {
    backgroundColor: '#1c1c1e',
    border: '1px solid #2a2a2e',
    color: '#c4c0b8',
  }

  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ borderTop: '1px solid #232326', backgroundColor: '#0d0d0e' }}
    >
      <p className="text-[12px]" style={{ color: '#555558' }}>
        Page <span style={{ color: '#c4c0b8' }} className="font-medium">{page}</span> of{' '}
        <span style={{ color: '#c4c0b8' }} className="font-medium">{pages}</span> &mdash;{' '}
        <span style={{ color: '#c4c0b8' }} className="font-medium">{total}</span> records
      </p>
      <div className="flex gap-1.5">
        <button
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[12px] font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
          style={btnBase}
        >
          <ChevronLeft className="h-3.5 w-3.5" /> Prev
        </button>
        <button
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[12px] font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
          style={btnBase}
        >
          Next <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
