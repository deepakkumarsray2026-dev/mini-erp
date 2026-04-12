import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { payrollService } from '../../../services/payroll.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { PayPeriod } from '../../../types/payroll.types'
import { format } from 'date-fns'

const columns: Column<PayPeriod>[] = [
  { key: 'period_name', header: 'Period', render: (r) => <span className="font-medium">{r.period_name}</span> },
  { key: 'pay_group_name', header: 'Pay Group', render: (r) => r.pay_group_name ?? '—' },
  { key: 'start_date', header: 'Start', render: (r) => format(new Date(r.start_date), 'MMM d, yyyy') },
  { key: 'end_date', header: 'End', render: (r) => format(new Date(r.end_date), 'MMM d, yyyy') },
  { key: 'pay_date', header: 'Pay Date', render: (r) => format(new Date(r.pay_date), 'MMM d, yyyy') },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

export default function PayPeriodsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['pay-periods', page],
    queryFn: () => payrollService.getPayPeriods(page, 20),
  })

  return (
    <div>
      <PageHeader title="Pay Periods" description={`${data?.total ?? 0} pay periods`} />
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
