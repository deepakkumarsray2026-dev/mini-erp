export interface ExpenseCategory {
  id: string
  name: string
  code: string
  daily_limit: number | null
  is_active: boolean
}

export interface ExpenseReport {
  id: string
  report_number: string
  employee_id: string
  employee_name: string | null
  title: string
  description: string | null
  total_amount: number
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'paid'
  submitted_at: string | null
  created_at: string
}
