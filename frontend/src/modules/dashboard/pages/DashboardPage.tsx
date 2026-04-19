import { useQuery } from '@tanstack/react-query'
import { Users, DollarSign, ShoppingCart, Receipt, FileText } from 'lucide-react'
import { workforceService } from '../../../services/workforce.service'
import { apService } from '../../../services/ap.service'
import { expensesService } from '../../../services/expenses.service'
import { procurementService } from '../../../services/procurement.service'
import { Spinner } from '../../../components/common/Spinner'

function StatCard({
  label,
  value,
  icon,
  iconBg,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  iconBg: string
}) {
  return (
    <div
      className="flex items-center gap-4 rounded-xl p-5"
      style={{ backgroundColor: '#1c1c1e', border: '1px solid #2a2a2e' }}
    >
      <div
        className="flex h-12 w-12 items-center justify-center rounded-xl flex-shrink-0"
        style={{ backgroundColor: iconBg }}
      >
        {icon}
      </div>
      <div>
        <p className="text-sm" style={{ color: '#6b6b6b' }}>{label}</p>
        <p className="text-2xl font-bold" style={{ color: '#f0ece3' }}>{value}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: employees, isLoading: l1 } = useQuery({
    queryKey: ['employees-count'],
    queryFn: () => workforceService.getEmployees(1, 1),
  })
  const { data: invoices, isLoading: l2 } = useQuery({
    queryKey: ['invoices-count'],
    queryFn: () => apService.getInvoices(1, 1),
  })
  const { data: expenses, isLoading: l3 } = useQuery({
    queryKey: ['expenses-count'],
    queryFn: () => expensesService.getReports(1, 1),
  })
  const { data: orders, isLoading: l4 } = useQuery({
    queryKey: ['orders-count'],
    queryFn: () => procurementService.getPurchaseOrders(1, 1),
  })

  const loading = l1 || l2 || l3 || l4

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold" style={{ color: '#f0ece3' }}>Dashboard</h2>
        <p className="mt-1 text-sm" style={{ color: '#6b6b6b' }}>Overview of your ERP data</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Employees"
            value={employees?.total ?? 0}
            icon={<Users className="h-6 w-6" style={{ color: '#d97757' }} />}
            iconBg="rgba(217,119,87,0.12)"
          />
          <StatCard
            label="AP Invoices"
            value={invoices?.total ?? 0}
            icon={<FileText className="h-6 w-6" style={{ color: '#8888df' }} />}
            iconBg="rgba(136,136,223,0.12)"
          />
          <StatCard
            label="Expense Reports"
            value={expenses?.total ?? 0}
            icon={<Receipt className="h-6 w-6" style={{ color: '#dfba80' }} />}
            iconBg="rgba(223,186,128,0.12)"
          />
          <StatCard
            label="Purchase Orders"
            value={orders?.total ?? 0}
            icon={<ShoppingCart className="h-6 w-6" style={{ color: '#7abf7a' }} />}
            iconBg="rgba(122,191,122,0.12)"
          />
        </div>
      )}

      <div
        className="mt-6 rounded-xl p-6"
        style={{ backgroundColor: '#1c1c1e', border: '1px solid #2a2a2e' }}
      >
        <h3 className="text-base font-semibold mb-3" style={{ color: '#f0ece3' }}>Getting Started</h3>
        <ul className="space-y-2 text-sm" style={{ color: '#6b6b6b' }}>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#d97757' }} />
            Browse employees in <strong style={{ color: '#c4c0b8' }}>Workforce → Employees</strong>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#d97757' }} />
            Review invoices in <strong style={{ color: '#c4c0b8' }}>Accounts Payable → Invoices</strong>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#d97757' }} />
            Check payslips in <strong style={{ color: '#c4c0b8' }}>Payroll → Payslips</strong>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#d97757' }} />
            View the trial balance in <strong style={{ color: '#c4c0b8' }}>General Ledger → Trial Balance</strong>
          </li>
        </ul>
      </div>
    </div>
  )
}
