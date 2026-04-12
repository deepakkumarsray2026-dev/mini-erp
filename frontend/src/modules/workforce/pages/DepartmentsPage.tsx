import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { workforceService } from '../../../services/workforce.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Department } from '../../../types/workforce.types'

const columns: Column<Department>[] = [
  { key: 'code', header: 'Code', className: 'w-24 font-mono text-xs' },
  { key: 'name', header: 'Name', render: (r) => <span className="font-medium">{r.name}</span> },
  { key: 'description', header: 'Description', render: (r) => r.description ?? '—' },
  {
    key: 'is_active', header: 'Status',
    render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
  },
]

export default function DepartmentsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['departments', page],
    queryFn: () => workforceService.getDepartments(page, 20),
  })

  return (
    <div>
      <PageHeader title="Departments" description={`${data?.total ?? 0} departments`} />
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
