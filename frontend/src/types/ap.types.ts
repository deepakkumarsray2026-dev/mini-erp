export interface Vendor {
  id: string
  vendor_id: string
  name: string
  email: string | null
  phone: string | null
  tax_id: string | null
  payment_terms_days: number
  is_active: boolean
  created_at: string
}

export interface Invoice {
  id: string
  invoice_number: string
  vendor_id: string
  vendor_name: string | null
  invoice_date: string
  due_date: string
  total_amount: number
  paid_amount: number
  status: 'draft' | 'submitted' | 'approved' | 'paid' | 'cancelled' | 'overdue'
  description: string | null
  created_at: string
}
