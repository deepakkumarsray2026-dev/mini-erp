import { useQuery } from '@tanstack/react-query'
import { glService } from '../../../services/gl.service'
import { Spinner } from '../../../components/common/Spinner'
import { Badge } from '../../../components/common/Badge'
import { PageHeader } from '../../../components/layout/PageHeader'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

const typeColors: Record<string, 'blue' | 'red' | 'green' | 'purple' | 'orange'> = {
  asset: 'blue', liability: 'red', equity: 'purple', revenue: 'green', expense: 'orange',
}

export default function TrialBalancePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['trial-balance'],
    queryFn: () => glService.getTrialBalance(),
  })

  const totalDebits = data?.reduce((s, r) => s + Number(r.total_debit), 0) ?? 0
  const totalCredits = data?.reduce((s, r) => s + Number(r.total_credit), 0) ?? 0
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01

  return (
    <div>
      <PageHeader
        title="Trial Balance"
        description="As of current date"
        actions={
          data && (
            <Badge variant={isBalanced ? 'green' : 'red'}>
              {isBalanced ? 'Balanced' : 'Out of Balance'}
            </Badge>
          )
        }
      />
      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Account</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Type</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">Debit</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">Credit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data ?? []).map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono text-xs text-gray-600">{row.account_code}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{row.account_name}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge variant={typeColors[row.account_type] ?? 'gray'}>{row.account_type}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-right">
                    {Number(row.total_debit) > 0 ? fmt(Number(row.total_debit)) : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-right">
                    {Number(row.total_credit) > 0 ? fmt(Number(row.total_credit)) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 font-semibold">
              <tr>
                <td colSpan={3} className="px-4 py-3 text-sm text-gray-700">Totals</td>
                <td className="px-4 py-3 text-sm font-mono text-right text-gray-900">{fmt(totalDebits)}</td>
                <td className="px-4 py-3 text-sm font-mono text-right text-gray-900">{fmt(totalCredits)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  )
}
