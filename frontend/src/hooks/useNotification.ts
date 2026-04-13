import { useStore } from '../store'

export function useNotification() {
  const add = useStore((s) => s.addNotification)
  return {
    success: (message: string) => add({ type: 'success', message }),
    error: (message: string) => add({ type: 'error', message }),
    info: (message: string) => add({ type: 'info', message }),
  }
}

/** Extract a human-readable error message from an axios error */
export function getErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } } }
  const detail = e?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((d: { msg?: string }) => d.msg ?? String(d)).join('; ')
  }
  if (typeof detail === 'string') return detail
  if (detail) return String(detail)
  return 'An unexpected error occurred'
}
