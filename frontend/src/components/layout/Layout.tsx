import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { ToastContainer } from '../common/Toast'

const titleMap: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/workforce/employees': 'Employees',
  '/workforce/departments': 'Departments',
  '/payroll/periods': 'Pay Periods',
  '/payroll/payslips': 'Payslips',
  '/ap/vendors': 'Vendors',
  '/ap/invoices': 'Invoices',
  '/expenses/reports': 'Expense Reports',
  '/procurement/requisitions': 'Requisitions',
  '/procurement/orders': 'Purchase Orders',
  '/gl/accounts': 'Chart of Accounts',
  '/gl/journals': 'Journals',
  '/gl/trial-balance': 'Trial Balance',
  '/admin/users': 'Users',
  '/ai': 'AI / MLOps',
}

export function Layout() {
  const { pathname } = useLocation()
  const title = titleMap[pathname] ?? 'Mini ERP'
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav title={title} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
      <ToastContainer />
    </div>
  )
}
