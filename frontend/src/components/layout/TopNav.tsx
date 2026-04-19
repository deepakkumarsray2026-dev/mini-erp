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
    <header className="flex h-14 items-center justify-between border-b border-gray-200/80 bg-white/80 backdrop-blur-sm px-6 sticky top-0 z-10">
      <h1 className="text-sm font-semibold text-gray-900 tracking-tight">{title}</h1>

      <div className="flex items-center gap-3">
        {/* User chip */}
        <div className="flex items-center gap-2.5 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white flex-shrink-0">
            {initials(displayName)}
          </div>
          <span className="text-[13px] font-medium text-gray-700">{displayName}</span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </header>
  )
}
