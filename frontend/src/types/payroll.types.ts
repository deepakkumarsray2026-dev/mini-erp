export interface PayPeriod {
  id: string
  pay_group_id: string
  pay_group_name: string | null
  period_name: string
  start_date: string
  end_date: string
  pay_date: string
  status: 'open' | 'processing' | 'closed' | 'cancelled'
  created_at: string
}

export interface Payslip {
  id: string
  employee_id: string
  employee_name: string | null
  pay_period_id: string
  period_name: string | null
  gross_pay: number
  total_deductions: number
  net_pay: number
  status: 'draft' | 'approved' | 'paid' | 'cancelled'
  created_at: string
}
