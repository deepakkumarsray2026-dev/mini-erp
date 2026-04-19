import { useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { useStore } from '../../store'

const icons = {
  success: <CheckCircle className="h-5 w-5 text-green-600" />,
  error:   <AlertCircle className="h-5 w-5 text-red-500" />,
  info:    <Info className="h-5 w-5 text-blue-600" />,
  warning: <AlertCircle className="h-5 w-5 text-amber-500" />,
}

function ToastItem({ id, type, message }: { id: string; type: 'success' | 'error' | 'info' | 'warning'; message: string }) {
  const remove = useStore((s) => s.removeNotification)
  useEffect(() => {
    const t = setTimeout(() => remove(id), 4000)
    return () => clearTimeout(t)
  }, [id, remove])

  return (
    <div
      className="flex items-start gap-3 rounded-xl p-4 shadow-lg"
      style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E6EA' }}
    >
      {icons[type]}
      <p className="flex-1 text-sm" style={{ color: '#111827' }}>{message}</p>
      <button
        onClick={() => remove(id)}
        className="rounded p-0.5 transition-colors"
        style={{ color: '#9CA3AF' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#F3F4F6')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export function ToastContainer() {
  const notifications = useStore((s) => s.notifications)
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
      {notifications.map((n) => (
        <ToastItem key={n.id} {...n} />
      ))}
    </div>
  )
}
