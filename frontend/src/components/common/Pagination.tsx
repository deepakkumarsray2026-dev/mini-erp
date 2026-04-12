import { Button } from './Button'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
      <p className="text-sm text-gray-500">
        Page {page} of {pages} &mdash; {total} total
      </p>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Previous
        </Button>
        <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  )
}
