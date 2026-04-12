import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { procurementService } from '../../../services/procurement.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Requisition } from '../../../types/procurement.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<Requisition>[] = [
  { key: 'requisition_number', header: 'Req #', className: 'font-mono text-xs' },
  { key: 'title', header: 'Title', render: (r) => <span className="font-medium">{r.title}</span> },
  { key: 'requester_name', header: 'Requester', render: (r) => r.requester_name ?? '—' },
  { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
  {
    key: 'required_date', header: 'Required By',
    render: (r) => r.required_date ? format(new Date(r.required_date), 'MMM d, yyyy') : '—',
  },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

const statuses = ['', 'draft', 'submitted', 'approved', 'rejected', 'converted', 'cancelled']

export default function RequisitionsPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['requisitions', page, status],
    queryFn: () => procurementService.getRequisitions(page, 20, status || undefined),
  })

  return (
    <div>
      <PageHeader title="Purchase Requisitions" description={`${data?.total ?? 0} requisitions`} />
      <div className="mb-4">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          {statuses.map((s) => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
      </div>
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
