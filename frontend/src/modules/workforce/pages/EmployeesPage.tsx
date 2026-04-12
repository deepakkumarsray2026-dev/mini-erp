import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { workforceService } from '../../../services/workforce.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge, statusBadge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Employee } from '../../../types/workforce.types'
import { format } from 'date-fns'

const columns: Column<Employee>[] = [
  { key: 'employee_number', header: 'ID', className: 'w-28 font-mono text-xs' },
  {
    key: 'full_name', header: 'Name',
    render: (r) => (
      <div>
        <p className="font-medium text-gray-900">{r.full_name}</p>
        <p className="text-xs text-gray-400">{r.email}</p>
      </div>
    ),
  },
  { key: 'department_name', header: 'Department', render: (r) => r.department_name ?? '—' },
  { key: 'job_title', header: 'Job Title', render: (r) => r.job_title ?? '—' },
  {
    key: 'hire_date', header: 'Hire Date',
    render: (r) => format(new Date(r.hire_date), 'MMM d, yyyy'),
  },
  {
    key: 'employment_status', header: 'Status',
    render: (r) => (
      <Badge variant={statusBadge(r.employment_status)}>
        {r.employment_status.replace('_', ' ')}
      </Badge>
    ),
  },
]

export default function EmployeesPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['employees', page, debouncedSearch],
    queryFn: () => workforceService.getEmployees(page, 20, debouncedSearch || undefined),
  })

  const handleSearch = (v: string) => {
    setSearch(v)
    clearTimeout((window as unknown as { _st?: number })._st)
    ;(window as unknown as { _st?: number })._st = setTimeout(() => {
      setDebouncedSearch(v)
      setPage(1)
    }, 400) as unknown as number
  }

  return (
    <div>
      <PageHeader title="Employees" description={`${data?.total ?? 0} total employees`} />
      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by name or email…"
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
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
