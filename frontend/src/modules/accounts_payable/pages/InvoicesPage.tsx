import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apService } from '../../../services/ap.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Invoice } from '../../../types/ap.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<Invoice>[] = [
  { key: 'invoice_number', header: 'Invoice #', className: 'font-mono text-xs' },
  { key: 'vendor_name', header: 'Vendor', render: (r) => <span className="font-medium">{r.vendor_name ?? '—'}</span> },
  { key: 'invoice_date', header: 'Date', render: (r) => format(new Date(r.invoice_date), 'MMM d, yyyy') },
  { key: 'due_date', header: 'Due', render: (r) => format(new Date(r.due_date), 'MMM d, yyyy') },
  { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
  { key: 'paid_amount', header: 'Paid', render: (r) => <span className="font-mono text-green-700">{fmt(r.paid_amount)}</span> },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

const statuses = ['', 'draft', 'submitted', 'approved', 'paid', 'overdue', 'cancelled']

export default function InvoicesPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, status],
    queryFn: () => apService.getInvoices(page, 20, status || undefined),
  })

  return (
    <div>
      <PageHeader title="Invoices" description={`${data?.total ?? 0} invoices`} />
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
