import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { payrollService } from '../../../services/payroll.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Payslip } from '../../../types/payroll.types'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const columns: Column<Payslip>[] = [
  { key: 'employee_name', header: 'Employee', render: (r) => <span className="font-medium">{r.employee_name ?? '—'}</span> },
  { key: 'period_name', header: 'Period', render: (r) => r.period_name ?? '—' },
  { key: 'gross_pay', header: 'Gross Pay', render: (r) => <span className="font-mono">{fmt(r.gross_pay)}</span> },
  { key: 'total_deductions', header: 'Deductions', render: (r) => <span className="font-mono text-red-600">{fmt(r.total_deductions)}</span> },
  { key: 'net_pay', header: 'Net Pay', render: (r) => <span className="font-mono font-semibold text-green-700">{fmt(r.net_pay)}</span> },
  {
    key: 'status', header: 'Status',
    render: (r) => <Badge variant={statusBadge(r.status)}>{r.status}</Badge>,
  },
]

export default function PayslipsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['payslips', page],
    queryFn: () => payrollService.getPayslips(page, 20),
  })

  return (
    <div>
      <PageHeader title="Payslips" description={`${data?.total ?? 0} payslips`} />
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
