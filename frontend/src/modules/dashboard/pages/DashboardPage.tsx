import { useQuery } from '@tanstack/react-query'
import { Users, DollarSign, ShoppingCart, Receipt, TrendingUp, FileText } from 'lucide-react'
import { workforceService } from '../../../services/workforce.service'
import { apService } from '../../../services/ap.service'
import { expensesService } from '../../../services/expenses.service'
import { procurementService } from '../../../services/procurement.service'
import { Spinner } from '../../../components/common/Spinner'

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: React.ReactNode; color: string }) {
  return (
    <div className="flex items-center gap-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200">
      <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
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
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">Overview of your ERP data</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Employees"
            value={employees?.total ?? 0}
            icon={<Users className="h-6 w-6 text-blue-600" />}
            color="bg-blue-50"
          />
          <StatCard
            label="AP Invoices"
            value={invoices?.total ?? 0}
            icon={<FileText className="h-6 w-6 text-purple-600" />}
            color="bg-purple-50"
          />
          <StatCard
            label="Expense Reports"
            value={expenses?.total ?? 0}
            icon={<Receipt className="h-6 w-6 text-orange-600" />}
            color="bg-orange-50"
          />
          <StatCard
            label="Purchase Orders"
            value={orders?.total ?? 0}
            icon={<ShoppingCart className="h-6 w-6 text-green-600" />}
            color="bg-green-50"
          />
        </div>
      )}

      <div className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h3 className="text-base font-semibold text-gray-800 mb-3">Getting Started</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" /> Browse employees in <strong>Workforce → Employees</strong></li>
          <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" /> Review invoices in <strong>Accounts Payable → Invoices</strong></li>
          <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" /> Check payslips in <strong>Payroll → Payslips</strong></li>
          <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" /> View the trial balance in <strong>General Ledger → Trial Balance</strong></li>
        </ul>
      </div>
    </div>
  )
}
