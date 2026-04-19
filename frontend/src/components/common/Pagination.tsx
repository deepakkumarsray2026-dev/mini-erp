import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null

  const btnStyle: React.CSSProperties = {
    backgroundColor: '#FFFFFF',
    border: '1px solid #D1D5DB',
    color: '#374151',
  }

  return (
    <div
      className="flex items-center justify-between px-4 py-3"
      style={{ borderTop: '1px solid #E2E6EA', backgroundColor: '#F8F9FB' }}
    >
      <p className="text-[12px]" style={{ color: '#9CA3AF' }}>
        Page <span className="font-medium" style={{ color: '#374151' }}>{page}</span> of{' '}
        <span className="font-medium" style={{ color: '#374151' }}>{pages}</span> &mdash;{' '}
        <span className="font-medium" style={{ color: '#374151' }}>{total}</span> records
      </p>
      <div className="flex gap-1.5">
        <button
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[12px] font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          style={btnStyle}
          onMouseEnter={e => !e.currentTarget.disabled && (e.currentTarget.style.backgroundColor = '#F3F4F6')}
          onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
        >
          <ChevronLeft className="h-3.5 w-3.5" /> Prev
        </button>
        <button
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[12px] font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          style={btnStyle}
          onMouseEnter={e => !e.currentTarget.disabled && (e.currentTarget.style.backgroundColor = '#F3F4F6')}
          onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
        >
          Next <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
