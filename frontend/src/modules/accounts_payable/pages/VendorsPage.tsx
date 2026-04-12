import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { apService } from '../../../services/ap.service'
import { DataTable, type Column } from '../../../components/tables/DataTable'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'
import type { Vendor } from '../../../types/ap.types'

const columns: Column<Vendor>[] = [
  { key: 'code', header: 'Code', className: 'w-24 font-mono text-xs' },
  { key: 'name', header: 'Name', render: (r) => <span className="font-medium">{r.name}</span> },
  { key: 'email', header: 'Email', render: (r) => r.email ?? '—' },
  { key: 'phone', header: 'Phone', render: (r) => r.phone ?? '—' },
  { key: 'payment_terms', header: 'Terms', render: (r) => `Net ${r.payment_terms}` },
  {
    key: 'is_active', header: 'Status',
    render: (r) => <Badge variant={r.is_active ? 'green' : 'gray'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
  },
]

export default function VendorsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['vendors', page, debouncedSearch],
    queryFn: () => apService.getVendors(page, 20, debouncedSearch || undefined),
  })

  const handleSearch = (v: string) => {
    setSearch(v)
    clearTimeout((window as unknown as { _vst?: number })._vst)
    ;(window as unknown as { _vst?: number })._vst = setTimeout(() => {
      setDebouncedSearch(v)
      setPage(1)
    }, 400) as unknown as number
  }

  return (
    <div>
      <PageHeader title="Vendors" description={`${data?.total ?? 0} vendors`} />
      <div className="mb-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search vendors…"
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
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
