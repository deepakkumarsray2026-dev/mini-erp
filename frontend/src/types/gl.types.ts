export interface Account {
  id: string
  account_code: string
  account_name: string
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
  parent_id: string | null
  is_active: boolean
  normal_balance: 'debit' | 'credit'
  created_at: string
}

export interface Journal {
  id: string
  journal_number: string
  journal_date: string
  description: string
  source: string | null
  total_debit: number
  total_credit: number
  status: 'draft' | 'posted' | 'reversed'
  created_by: string | null
  created_at: string
}

export interface TrialBalanceEntry {
  account_code: string
  account_name: string
  account_type: string
  total_debit: number
  total_credit: number
}
