import { useEffect } from 'react'
import { X } from 'lucide-react'

interface Props {
  open: boolean
  title: string
  onClose: () => void
  children: React.ReactNode
  footer?: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export function Modal({ open, title, onClose, children, footer, size = 'md' }: Props) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  const widths = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl' }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div
        className={`relative w-full ${widths[size]} rounded-2xl shadow-2xl flex flex-col max-h-[90vh]`}
        style={{ backgroundColor: '#1c1c1e', border: '1px solid #2a2a2e' }}
      >
        <div
          className="flex items-center justify-between px-6 py-4 flex-shrink-0"
          style={{ borderBottom: '1px solid #232326' }}
        >
          <h2 className="text-[15px] font-semibold tracking-tight" style={{ color: '#f0ece3' }}>{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 transition-colors"
            style={{ color: '#555558' }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = '#222224'
              e.currentTarget.style.color = '#c4c0b8'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'transparent'
              e.currentTarget.style.color = '#555558'
            }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">{children}</div>
        {footer && (
          <div
            className="flex justify-end gap-2.5 px-6 py-4 flex-shrink-0"
            style={{ borderTop: '1px solid #232326' }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Shared form helpers ────────────────────────────────────────────────────────

export const inputCls =
  'w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50 bg-[#111113] border border-[#2e2e32] text-[#f0ece3] placeholder:text-[#555558] focus:border-[#d97757]'

// inputCls needs inline styles — use inputStyle alongside inputCls
export const inputStyle: React.CSSProperties = {
  backgroundColor: '#111113',
  border: '1px solid #2e2e32',
  color: '#f0ece3',
}

// Helper to merge focus border — use onFocus/onBlur on the element
export const inputFocusHandlers = {
  onFocus: (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = '#d97757'
  },
  onBlur: (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = '#2e2e32'
  },
}

interface FieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

export function Field({ label, error, required, children }: FieldProps) {
  return (
    <div>
      <label className="block text-[13px] font-medium mb-1.5" style={{ color: '#c4c0b8' }}>
        {label}{required && <span className="ml-0.5" style={{ color: '#df9090' }}>*</span>}
      </label>
      {children}
      {error && <p className="mt-1.5 text-xs" style={{ color: '#df9090' }}>{error}</p>}
    </div>
  )
}

export function FormActions({
  onCancel,
  loading,
  submitLabel = 'Save',
}: {
  onCancel: () => void
  loading?: boolean
  submitLabel?: string
}) {
  return (
    <div className="flex justify-end gap-2.5 mt-6 pt-4" style={{ borderTop: '1px solid #232326' }}>
      <button
        type="button"
        onClick={onCancel}
        className="px-4 py-2 text-[13px] font-medium rounded-lg transition-colors"
        style={{ color: '#c4c0b8', backgroundColor: '#1c1c1e', border: '1px solid #2a2a2e' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#222224')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#1c1c1e')}
      >
        Cancel
      </button>
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 text-[13px] font-medium text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
        style={{ backgroundColor: '#d97757' }}
        onMouseEnter={e => !loading && (e.currentTarget.style.opacity = '0.88')}
        onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
      >
        {loading ? 'Saving…' : submitLabel}
      </button>
    </div>
  )
}
