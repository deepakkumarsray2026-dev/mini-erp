import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import LoginPage from './modules/auth/pages/LoginPage'
import DashboardPage from './modules/dashboard/pages/DashboardPage'
import EmployeesPage from './modules/workforce/pages/EmployeesPage'
import DepartmentsPage from './modules/workforce/pages/DepartmentsPage'
import PayPeriodsPage from './modules/payroll/pages/PayPeriodsPage'
import PayslipsPage from './modules/payroll/pages/PayslipsPage'
import VendorsPage from './modules/accounts_payable/pages/VendorsPage'
import InvoicesPage from './modules/accounts_payable/pages/InvoicesPage'
import ExpenseReportsPage from './modules/expenses/pages/ExpenseReportsPage'
import RequisitionsPage from './modules/procurement/pages/RequisitionsPage'
import PurchaseOrdersPage from './modules/procurement/pages/PurchaseOrdersPage'
import AccountsPage from './modules/general_ledger/pages/AccountsPage'
import JournalsPage from './modules/general_ledger/pages/JournalsPage'
import TrialBalancePage from './modules/general_ledger/pages/TrialBalancePage'
import UsersPage from './modules/admin/pages/UsersPage'
import AIDashboardPage from './modules/ai_dashboard/pages/AIDashboardPage'
import ChatPage from './modules/chat/pages/ChatPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/workforce/employees', element: <EmployeesPage /> },
      { path: '/workforce/departments', element: <DepartmentsPage /> },
      { path: '/payroll/periods', element: <PayPeriodsPage /> },
      { path: '/payroll/payslips', element: <PayslipsPage /> },
      { path: '/ap/vendors', element: <VendorsPage /> },
      { path: '/ap/invoices', element: <InvoicesPage /> },
      { path: '/expenses/reports', element: <ExpenseReportsPage /> },
      { path: '/procurement/requisitions', element: <RequisitionsPage /> },
      { path: '/procurement/orders', element: <PurchaseOrdersPage /> },
      { path: '/gl/accounts', element: <AccountsPage /> },
      { path: '/gl/journals', element: <JournalsPage /> },
      { path: '/gl/trial-balance', element: <TrialBalancePage /> },
      { path: '/admin/users', element: <UsersPage /> },
      { path: '/ai', element: <AIDashboardPage /> },
      { path: '/chat', element: <ChatPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
