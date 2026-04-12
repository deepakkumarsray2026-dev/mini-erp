import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { glService } from '../../../services/gl.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Journal } from '../../../types/gl.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<Journal>[] = [
  { key: 'journal_number', header: 'Journal #', className: 'font-mono text-xs' },
  { key: 'journal_date', header: 'Date', render: (r) => format(new Date(r.journal_date), 'MMM d, yyyy') },
  { key: 'description', header: 'Description', render: (r) => <span className="font-medium">{r.description}</span> },
  { key: 'reference', header: 'Reference', render: (r) => r.reference ?? '—' },
  { key: 'total_debits', header: 'Debits', render: (r) => <span className="font-mono">{fmt(r.total_debits)}</span> },
  { key: 'total_credits', header: 'Credits', render: (r) => <span className="font-mono">{fmt(r.total_credits)}</span> },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

export default function JournalsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['journals', page],
    queryFn: () => glService.getJournals(page, 20),
  })

  return (
    <div>
      <PageHeader title="Journal Entries" description={`${data?.total ?? 0} journals`} />
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        page={page}
        pages={data?.pages}
        total={data?.total}
        onPage={setPage}
      />
    </div>
  )
}
