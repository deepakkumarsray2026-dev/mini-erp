import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { procurementService } from '../../../services/procurement.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { PurchaseOrder } from '../../../types/procurement.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<PurchaseOrder>[] = [
  { key: 'po_number', header: 'PO #', className: 'font-mono text-xs' },
  { key: 'vendor_name', header: 'Vendor', render: (r) => <span className="font-medium">{r.vendor_name ?? '—'}</span> },
  { key: 'order_date', header: 'Order Date', render: (r) => format(new Date(r.order_date), 'MMM d, yyyy') },
  {
    key: 'expected_delivery_date', header: 'Delivery',
    render: (r) => r.expected_delivery_date ? format(new Date(r.expected_delivery_date), 'MMM d, yyyy') : '—',
  },
  { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status.replace('_', ' ')}</Badge>,
  },
]

const statuses = ['', 'draft', 'sent', 'acknowledged', 'partially_received', 'received', 'cancelled']

export default function PurchaseOrdersPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', page, status],
    queryFn: () => procurementService.getPurchaseOrders(page, 20, status || undefined),
  })

  return (
    <div>
      <PageHeader title="Purchase Orders" description={`${data?.total ?? 0} purchase orders`} />
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
