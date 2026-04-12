import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { glService } from '../../../services/gl.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Account } from '../../../types/gl.types'

const typeColors: Record<string, 'blue' | 'red' | 'green' | 'purple' | 'orange'> = {
  asset: 'blue', liability: 'red', equity: 'purple', revenue: 'green', expense: 'orange',
}

const columns: Column<Account>[] = [
  { key: 'account_number', header: 'Number', className: 'w-28 font-mono text-xs' },
  { key: 'account_name', header: 'Name', render: (r) => <span className="font-medium">{r.account_name}</span> },
  {
    key: 'account_type', header: 'Type',
    render: (r) => <Badge variant={typeColors[r.account_type] ?? 'gray'}>{r.account_type}</Badge>,
  },
  { key: 'normal_balance', header: 'Normal Balance', render: (r) => r.normal_balance },
  {
    key: 'is_active', header: 'Status',
    render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
  },
]

export default function AccountsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['gl-accounts', page],
    queryFn: () => glService.getAccounts(page, 50),
  })

  return (
    <div>
      <PageHeader title="Chart of Accounts" description={`${data?.total ?? 0} accounts`} />
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
