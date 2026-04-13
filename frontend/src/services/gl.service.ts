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

  async getAllAccounts(): Promise<Account[]> {
    const res = await api.get<PaginatedResponse<Account>>('/gl/accounts', {
      params: { page: 1, page_size: 200 },
    })
    return res.data.items
  },

  async getFiscalPeriods(): Promise<{ id: string; name: string; fiscal_year: number; period_number: number }[]> {
    const res = await api.get('/gl/fiscal-periods')
    return res.data
  },

  async createAccount(data: Record<string, unknown>): Promise<Account> {
    const res = await api.post<Account>('/gl/accounts', data)
    return res.data
  },

  async updateAccount(accountCode: string, data: Record<string, unknown>): Promise<Account> {
    const res = await api.patch<Account>(`/gl/accounts/${accountCode}`, data)
    return res.data
  },

  async getJournals(page = 1, size = 20): Promise<PaginatedResponse<Journal>> {
    const res = await api.get<PaginatedResponse<Journal>>('/gl/journals', {
      params: { page, size },
    })
    return res.data
  },

  async createJournal(data: Record<string, unknown>): Promise<Journal> {
    const res = await api.post<Journal>('/gl/journals', data)
    return res.data
  },

  async getTrialBalance(fiscalYear?: number): Promise<TrialBalanceEntry[]> {
    const res = await api.get<TrialBalanceEntry[]>('/gl/trial-balance', {
      params: fiscalYear ? { fiscal_year: fiscalYear } : {},
    })
    return res.data
  },
}
