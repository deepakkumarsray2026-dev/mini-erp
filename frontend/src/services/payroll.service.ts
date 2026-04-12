import api from './api'
import type { PayPeriod, Payslip } from '../types/payroll.types'
import type { PaginatedResponse } from '../types/common.types'

export const payrollService = {
  async getPayPeriods(page = 1, size = 20): Promise<PaginatedResponse<PayPeriod>> {
    const res = await api.get<PaginatedResponse<PayPeriod>>('/payroll/pay-periods', {
      params: { page, size },
    })
    return res.data
  },

  async getPayslips(page = 1, size = 20, employeeId?: string): Promise<PaginatedResponse<Payslip>> {
    const res = await api.get<PaginatedResponse<Payslip>>('/payroll/payslips', {
      params: { page, size, employee_id: employeeId },
    })
    return res.data
  },
}
