import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, Users, DollarSign, Receipt,
  ShoppingCart, BookOpen, Settings, ChevronDown, ChevronRight,
  CreditCard, Brain, Briefcase,
} from 'lucide-react'
import { useState } from 'react'

interface NavItem {
  label: string
  icon: React.ReactNode
  href?: string
  children?: { label: string; href: string }[]
}

interface NavSection {
  label: string
  items: NavItem[]
}

const sections: NavSection[] = [
  {
    label: 'Core',
    items: [
      { label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" />, href: '/dashboard' },
    ],
  },
  {
    label: 'People',
    items: [
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
    ],
  },
  {
    label: 'Finance',
    items: [
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
        label: 'General Ledger', icon: <BookOpen className="h-4 w-4" />,
        children: [
          { label: 'Chart of Accounts', href: '/gl/accounts' },
          { label: 'Journals', href: '/gl/journals' },
          { label: 'Trial Balance', href: '/gl/trial-balance' },
        ],
      },
    ],
  },
  {
    label: 'Operations',
    items: [
      {
        label: 'Procurement', icon: <ShoppingCart className="h-4 w-4" />,
        children: [
          { label: 'Requisitions', href: '/procurement/requisitions' },
          { label: 'Purchase Orders', href: '/procurement/orders' },
        ],
      },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'AI / MLOps', icon: <Brain className="h-4 w-4" />, href: '/ai' },
    ],
  },
  {
    label: 'System',
    items: [
      {
        label: 'Admin', icon: <Settings className="h-4 w-4" />,
        children: [
          { label: 'Users', href: '/admin/users' },
        ],
      },
    ],
  },
]

function NavGroup({ item }: { item: NavItem }) {
  const [open, setOpen] = useState(true)

  if (item.href) {
    return (
      <NavLink
        to={item.href}
        className={({ isActive }) =>
          clsx(
            'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-all',
            isActive
              ? 'bg-[#0057AE]/15 text-[#5BA4F5]'
              : 'text-[#94A3B8] hover:bg-white/8 hover:text-[#CBD5E1]',
          )
        }
      >
        {({ isActive }) => (
          <>
            <span className="flex-shrink-0 transition-colors" style={isActive ? { color: '#5BA4F5' } : {}}>
              {item.icon}
            </span>
            {item.label}
          </>
        )}
      </NavLink>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-all"
        style={{ color: '#94A3B8' }}
        onMouseEnter={e => {
          e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.06)'
          e.currentTarget.style.color = '#CBD5E1'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.backgroundColor = 'transparent'
          e.currentTarget.style.color = '#94A3B8'
        }}
      >
        <span className="flex-shrink-0">{item.icon}</span>
        <span className="flex-1 text-left">{item.label}</span>
        {open
          ? <ChevronDown className="h-3 w-3" style={{ color: '#4A6080' }} />
          : <ChevronRight className="h-3 w-3" style={{ color: '#4A6080' }} />}
      </button>
      {open && item.children && (
        <div className="ml-[26px] mt-0.5 flex flex-col pl-3 gap-0.5" style={{ borderLeft: '1px solid #2E4066' }}>
          {item.children.map((child) => (
            <NavLink
              key={child.href}
              to={child.href}
              className={({ isActive }) =>
                clsx(
                  'rounded-md px-2 py-1.5 text-[12.5px] transition-all',
                  isActive
                    ? 'font-semibold text-[#5BA4F5]'
                    : 'text-[#64748B] hover:text-[#CBD5E1]',
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
    <aside className="flex h-full w-56 flex-col" style={{ backgroundColor: '#1C2B4A', borderRight: '1px solid #243558' }}>
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-4" style={{ borderBottom: '1px solid #243558' }}>
        <div
          className="flex h-7 w-7 items-center justify-center rounded-lg"
          style={{ backgroundColor: '#0057AE' }}
        >
          <Briefcase className="h-4 w-4 text-white" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-white">Mini ERP</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="mb-1.5 px-2.5 text-[10px] font-semibold uppercase tracking-widest" style={{ color: '#4A6080' }}>
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavGroup key={item.label} item={item} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3" style={{ borderTop: '1px solid #243558' }}>
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <p className="text-[11px]" style={{ color: '#4A6080' }}>v2.0 · Phase 2 ML</p>
        </div>
      </div>
    </aside>
  )
}
