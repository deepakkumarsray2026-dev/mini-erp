import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { expensesService } from '../../../services/expenses.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { ExpenseReport } from '../../../types/expenses.types'
import { format } from 'date-fns'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<ExpenseReport>[] = [
  { key: 'report_number', header: 'Report #', className: 'font-mono text-xs' },
  { key: 'title', header: 'Title', render: (r) => <span className="font-medium">{r.title}</span> },
  { key: 'employee_name', header: 'Employee', render: (r) => r.employee_name ?? '—' },
  { key: 'total_amount', header: 'Amount', render: (r) => <span className="font-mono">{fmt(r.total_amount)}</span> },
  {
    key: 'submitted_at', header: 'Submitted',
    render: (r) => r.submitted_at ? format(new Date(r.submitted_at), 'MMM d, yyyy') : '—',
  },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

const statuses = ['', 'draft', 'submitted', 'approved', 'rejected', 'paid']

export default function ExpenseReportsPage() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['expense-reports', page, status],
    queryFn: () => expensesService.getReports(page, 20, status || undefined),
  })

  return (
    <div>
      <PageHeader title="Expense Reports" description={`${data?.total ?? 0} reports`} />
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
