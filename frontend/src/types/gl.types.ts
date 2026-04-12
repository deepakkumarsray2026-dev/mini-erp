export interface Account {
  id: string
  account_number: string
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
  reference: string | null
  total_debits: number
  total_credits: number
  status: 'draft' | 'posted' | 'reversed'
  created_by: string | null
  created_at: string
}

export interface TrialBalanceEntry {
  account_number: string
  account_name: string
  account_type: string
  debit_balance: number
  credit_balance: number
}
