import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useStore } from '../../store'
import { authService } from '../../services/auth.service'

interface Props {
  title: string
}

function initials(name: string) {
  return name
    .split(' ')
    .slice(0, 2)
    .map((n) => n[0])
    .join('')
    .toUpperCase()
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
      className="flex h-14 items-center justify-between px-6 sticky top-0 z-10 backdrop-blur-sm"
      style={{ backgroundColor: 'rgba(19,19,20,0.92)', borderBottom: '1px solid #232326' }}
    >
      <h1 className="text-sm font-semibold tracking-tight" style={{ color: '#f0ece3' }}>{title}</h1>

      <div className="flex items-center gap-3">
        {/* User chip */}
        <div
          className="flex items-center gap-2.5 rounded-lg px-3 py-1.5"
          style={{ border: '1px solid #2a2a2e', backgroundColor: '#1c1c1e' }}
        >
          <div
            className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold text-white flex-shrink-0"
            style={{ backgroundColor: '#d97757' }}
          >
            {initials(displayName)}
          </div>
          <span className="text-[13px] font-medium" style={{ color: '#c4c0b8' }}>{displayName}</span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors"
          style={{ color: '#6b6b6b' }}
          onMouseEnter={e => {
            e.currentTarget.style.backgroundColor = '#222224'
            e.currentTarget.style.color = '#f0ece3'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'transparent'
            e.currentTarget.style.color = '#6b6b6b'
          }}
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </header>
  )
}
