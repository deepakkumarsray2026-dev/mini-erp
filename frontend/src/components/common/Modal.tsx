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
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div
        className={`relative w-full ${widths[size]} rounded-2xl flex flex-col max-h-[90vh]`}
        style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E6EA', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}
      >
        <div
          className="flex items-center justify-between px-6 py-4 flex-shrink-0"
          style={{ borderBottom: '1px solid #F3F4F6' }}
        >
          <h2 className="text-[15px] font-semibold tracking-tight" style={{ color: '#111827' }}>{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 transition-colors"
            style={{ color: '#9CA3AF' }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = '#F3F4F6'
              e.currentTarget.style.color = '#374151'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'transparent'
              e.currentTarget.style.color = '#9CA3AF'
            }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">{children}</div>
        {footer && (
          <div
            className="flex justify-end gap-2.5 px-6 py-4 flex-shrink-0"
            style={{ borderTop: '1px solid #F3F4F6' }}
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
  'w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50 bg-white border border-[#D1D5DB] text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#0057AE] focus:ring-2 focus:ring-[#0057AE]/15'

interface FieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

export function Field({ label, error, required, children }: FieldProps) {
  return (
    <div>
      <label className="block text-[13px] font-medium mb-1.5" style={{ color: '#374151' }}>
        {label}{required && <span className="ml-0.5 text-red-500">*</span>}
      </label>
      {children}
      {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
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
    <div className="flex justify-end gap-2.5 mt-6 pt-4" style={{ borderTop: '1px solid #F3F4F6' }}>
      <button
        type="button"
        onClick={onCancel}
        className="px-4 py-2 text-[13px] font-medium rounded-lg transition-colors"
        style={{ color: '#374151', backgroundColor: '#FFFFFF', border: '1px solid #D1D5DB' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#F9FAFB')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
      >
        Cancel
      </button>
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 text-[13px] font-medium text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        style={{ backgroundColor: '#0057AE' }}
        onMouseEnter={e => !loading && (e.currentTarget.style.backgroundColor = '#004A9E')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#0057AE')}
      >
        {loading ? 'Saving…' : submitLabel}
      </button>
    </div>
  )
}
