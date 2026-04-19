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

const thStyle: React.CSSProperties = {
  backgroundColor: '#111113',
  color: '#555558',
  borderBottom: '1px solid #232326',
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
        <div
          className="overflow-hidden rounded-xl"
          style={{ border: '1px solid #2a2a2e', backgroundColor: '#1c1c1e' }}
        >
          <table className="min-w-full">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={thStyle}>Account</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={thStyle}>Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={thStyle}>Type</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide" style={thStyle}>Debit</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide" style={thStyle}>Credit</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((row, i) => (
                <tr
                  key={i}
                  style={{ borderTop: i > 0 ? '1px solid #232326' : undefined }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#222224')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td className="px-4 py-3 text-xs font-mono" style={{ color: '#6b6b6b' }}>{row.account_code}</td>
                  <td className="px-4 py-3 text-sm font-medium" style={{ color: '#f0ece3' }}>{row.account_name}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge variant={typeColors[row.account_type] ?? 'gray'}>{row.account_type}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-right" style={{ color: '#c4c0b8' }}>
                    {Number(row.total_debit) > 0 ? fmt(Number(row.total_debit)) : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-right" style={{ color: '#c4c0b8' }}>
                    {Number(row.total_credit) > 0 ? fmt(Number(row.total_credit)) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot style={{ borderTop: '1px solid #2a2a2e', backgroundColor: '#111113' }}>
              <tr>
                <td colSpan={3} className="px-4 py-3 text-sm font-semibold" style={{ color: '#c4c0b8' }}>Totals</td>
                <td className="px-4 py-3 text-sm font-mono text-right font-semibold" style={{ color: '#f0ece3' }}>{fmt(totalDebits)}</td>
                <td className="px-4 py-3 text-sm font-mono text-right font-semibold" style={{ color: '#f0ece3' }}>{fmt(totalCredits)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  )
}
