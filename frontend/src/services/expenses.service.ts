import api from './api'
import type { ExpenseReport } from '../types/expenses.types'
import type { PaginatedResponse } from '../types/common.types'

export const expensesService = {
  async getReports(page = 1, size = 20, status?: string): Promise<PaginatedResponse<ExpenseReport>> {
    const res = await api.get<PaginatedResponse<ExpenseReport>>('/expenses/reports', {
      params: { page, size, status },
    })
    return res.data
  },

  async createReport(data: Record<string, unknown>): Promise<ExpenseReport> {
    const res = await api.post<ExpenseReport>('/expenses/reports', data)
    return res.data
  },

  async approveReport(id: string): Promise<ExpenseReport> {
    const res = await api.post<ExpenseReport>(`/expenses/reports/${id}/approve`)
    return res.data
  },

  async rejectReport(id: string, reason: string): Promise<ExpenseReport> {
    const res = await api.post<ExpenseReport>(`/expenses/reports/${id}/reject`, { reason })
    return res.data
  },
}
