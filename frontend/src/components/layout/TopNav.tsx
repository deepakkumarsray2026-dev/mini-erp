import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useStore } from '../../store'
import { authService } from '../../services/auth.service'

interface Props {
  title: string
}

function initials(name: string) {
  return name.split(' ').slice(0, 2).map((n) => n[0]).join('').toUpperCase()
}

export function TopNav({ title }: Props) {
  const { user, logout } = useStore()
  const navigate = useNavigate()
  const displayName = user?.full_name ?? user?.username ?? 'User'

  const handleLogout = async () => {
    try { await authService.logout() } catch {}
    logout()
    navigate('/login')
  }

  return (
    <header
      className="flex h-14 items-center justify-between px-6 sticky top-0 z-10"
      style={{ backgroundColor: '#FFFFFF', borderBottom: '1px solid #E2E6EA', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}
    >
      <h1 className="text-sm font-semibold tracking-tight" style={{ color: '#111827' }}>{title}</h1>

      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-2.5 rounded-lg px-3 py-1.5"
          style={{ border: '1px solid #E2E6EA', backgroundColor: '#F8F9FB' }}
        >
          <div
            className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold text-white flex-shrink-0"
            style={{ backgroundColor: '#0057AE' }}
          >
            {initials(displayName)}
          </div>
          <span className="text-[13px] font-medium" style={{ color: '#374151' }}>{displayName}</span>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors"
          style={{ color: '#6B7280' }}
          onMouseEnter={e => {
            e.currentTarget.style.backgroundColor = '#F3F4F6'
            e.currentTarget.style.color = '#111827'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'transparent'
            e.currentTarget.style.color = '#6B7280'
          }}
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </header>
  )
}
