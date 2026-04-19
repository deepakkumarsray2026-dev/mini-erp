import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, Users, Building2, DollarSign, Receipt,
  ShoppingCart, BookOpen, Settings, ChevronDown, ChevronRight,
  Briefcase, FileText, CreditCard, TrendingUp, Brain,
} from 'lucide-react'
import { useState } from 'react'

interface NavItem {
  label: string
  icon: React.ReactNode
  href?: string
  children?: { label: string; href: string }[]
}

const nav: NavItem[] = [
  { label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" />, href: '/dashboard' },
  {
    label: 'Workforce', icon: <Users className="h-4 w-4" />,
    children: [
      { label: 'Employees', href: '/workforce/employees' },
      { label: 'Departments', href: '/workforce/departments' },
    ],
  },
  {
    label: 'Payroll', icon: <DollarSign className="h-4 w-4" />,
    children: [
      { label: 'Pay Periods', href: '/payroll/periods' },
      { label: 'Payslips', href: '/payroll/payslips' },
    ],
  },
  {
    label: 'Accounts Payable', icon: <CreditCard className="h-4 w-4" />,
    children: [
      { label: 'Vendors', href: '/ap/vendors' },
      { label: 'Invoices', href: '/ap/invoices' },
    ],
  },
  {
    label: 'Expenses', icon: <Receipt className="h-4 w-4" />,
    children: [
      { label: 'Reports', href: '/expenses/reports' },
    ],
  },
  {
    label: 'Procurement', icon: <ShoppingCart className="h-4 w-4" />,
    children: [
      { label: 'Requisitions', href: '/procurement/requisitions' },
      { label: 'Purchase Orders', href: '/procurement/orders' },
    ],
  },
  {
    label: 'General Ledger', icon: <BookOpen className="h-4 w-4" />,
    children: [
      { label: 'Chart of Accounts', href: '/gl/accounts' },
      { label: 'Journals', href: '/gl/journals' },
      { label: 'Trial Balance', href: '/gl/trial-balance' },
    ],
  },
  {
    label: 'Admin', icon: <Settings className="h-4 w-4" />,
    children: [
      { label: 'Users', href: '/admin/users' },
    ],
  },
  { label: 'AI / MLOps', icon: <Brain className="h-4 w-4" />, href: '/ai' },
]

function NavGroup({ item }: { item: NavItem }) {
  const [open, setOpen] = useState(true)
  if (item.href) {
    return (
      <NavLink
        to={item.href}
        className={({ isActive }) =>
          clsx(
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive ? 'bg-blue-700 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white',
          )
        }
      >
        {item.icon}
        {item.label}
      </NavLink>
    )
  }
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
      >
        {item.icon}
        <span className="flex-1 text-left">{item.label}</span>
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
      </button>
      {open && item.children && (
        <div className="ml-7 mt-1 flex flex-col gap-0.5">
          {item.children.map((child) => (
            <NavLink
              key={child.href}
              to={child.href}
              className={({ isActive }) =>
                clsx(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  isActive ? 'bg-blue-700 text-white font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-700',
                )
              }
            >
              {child.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 flex-col bg-slate-900">
      <div className="flex h-14 items-center gap-2 border-b border-slate-700 px-4">
        <Briefcase className="h-6 w-6 text-blue-400" />
        <span className="text-lg font-bold text-white tracking-tight">Mini ERP</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {nav.map((item) => (
          <NavGroup key={item.label} item={item} />
        ))}
      </nav>
      <div className="border-t border-slate-700 px-3 py-3">
        <p className="text-xs text-slate-500 text-center">v2.0 · Phase 2 ML</p>
      </div>
    </aside>
  )
}
