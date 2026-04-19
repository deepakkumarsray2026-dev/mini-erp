import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 bg-gray-50/50">
      <p className="text-[12px] text-gray-400">
        Page <span className="font-medium text-gray-600">{page}</span> of{' '}
        <span className="font-medium text-gray-600">{pages}</span> &mdash;{' '}
        <span className="font-medium text-gray-600">{total}</span> records
      </p>
      <div className="flex gap-1.5">
        <button
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-[12px] font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="h-3.5 w-3.5" /> Prev
        </button>
        <button
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
          className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-[12px] font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
