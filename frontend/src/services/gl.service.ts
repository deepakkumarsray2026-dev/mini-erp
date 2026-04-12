import api from './api'
import type { Account, Journal, TrialBalanceEntry } from '../types/gl.types'
import type { PaginatedResponse } from '../types/common.types'

export const glService = {
  async getAccounts(page = 1, size = 50): Promise<PaginatedResponse<Account>> {
    const res = await api.get<PaginatedResponse<Account>>('/gl/accounts', {
      params: { page, size },
    })
    return res.data
  },

  async getJournals(page = 1, size = 20): Promise<PaginatedResponse<Journal>> {
    const res = await api.get<PaginatedResponse<Journal>>('/gl/journals', {
      params: { page, size },
    })
    return res.data
  },

  async getTrialBalance(fiscalPeriodId?: string): Promise<TrialBalanceEntry[]> {
    const res = await api.get<TrialBalanceEntry[]>('/gl/trial-balance', {
      params: { fiscal_period_id: fiscalPeriodId },
    })
    return res.data
  },
}
