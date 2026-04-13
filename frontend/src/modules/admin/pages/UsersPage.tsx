import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../../services/api'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { User } from '../../../types/auth.types'
import { format } from 'date-fns'

const columns: Column<User>[] = [
  { key: 'username', header: 'Username', render: (r) => <span className="font-mono text-sm font-medium">{r.username}</span> },
  { key: 'full_name', header: 'Full Name', render: (r) => r.full_name },
  { key: 'email', header: 'Email' },
  {
    key: 'roles', header: 'Roles',
    render: (r) => (
      <div className="flex flex-wrap gap-1">
        {r.roles.length > 0 ? r.roles.map((role) => (
          <Badge key={role} variant="blue">{role}</Badge>
        )) : <span className="text-gray-400 text-xs">—</span>}
      </div>
    ),
  },
  {
    key: 'is_active', header: 'Status',
    render: (r) => (
      <div className="flex flex-wrap gap-1">
        <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>
        {r.is_superuser && <Badge variant="purple">Superuser</Badge>}
      </div>
    ),
  },
  { key: 'created_at', header: 'Created', render: (r) => r.created_at ? format(new Date(r.created_at), 'MMM d, yyyy') : '—' },
]

interface PaginatedUsers {
  items: User[]
  total: number
  page: number
  pages: number
}

export default function UsersPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: async () => {
      const res = await api.get<PaginatedUsers>('/auth/users', { params: { page, page_size: 20 } })
      return res.data
    },
  })

  const items = data?.items ?? []
  return (
    <div>
      <PageHeader title="Users" description={`${data?.total ?? 0} users`} />
      <DataTable
        columns={columns}
        data={items}
        loading={isLoading}
        page={page}
        pages={data?.pages}
        total={data?.total}
        onPage={setPage}
        emptyMessage="No users found."
      />
    </div>
  )
}
