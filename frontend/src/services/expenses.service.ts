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
}
