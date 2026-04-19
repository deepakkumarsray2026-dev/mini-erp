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
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative w-full ${widths[size]} bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh] ring-1 ring-gray-200/60`}>
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 flex-shrink-0">
          <h2 className="text-[15px] font-semibold text-gray-900 tracking-tight">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2.5 border-t border-gray-100 px-6 py-4 flex-shrink-0">{footer}</div>
        )}
      </div>
    </div>
  )
}

// ── Shared form helpers ────────────────────────────────────────────────────────

export const inputCls =
  'w-full rounded-lg border border-gray-200 bg-gray-50/50 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all disabled:bg-gray-50 disabled:text-gray-400'

interface FieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

export function Field({ label, error, required, children }: FieldProps) {
  return (
    <div>
      <label className="block text-[13px] font-medium text-gray-700 mb-1.5">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
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
    <div className="flex justify-end gap-2.5 mt-6 pt-4 border-t border-gray-100">
      <button
        type="button"
        onClick={onCancel}
        className="px-4 py-2 text-[13px] font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
      >
        Cancel
      </button>
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 text-[13px] font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
      >
        {loading ? 'Saving…' : submitLabel}
      </button>
    </div>
  )
}
