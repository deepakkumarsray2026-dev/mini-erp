import api from './api'
import type { Employee, Department } from '../types/workforce.types'
import type { PaginatedResponse } from '../types/common.types'

export const workforceService = {
  async getEmployees(page = 1, size = 20, search?: string): Promise<PaginatedResponse<Employee>> {
    const res = await api.get<PaginatedResponse<Employee>>('/workforce/employees', {
      params: { page, size, search },
    })
    return res.data
  },

  async getDepartments(page = 1, size = 50): Promise<PaginatedResponse<Department>> {
    const res = await api.get<PaginatedResponse<Department>>('/workforce/departments', {
      params: { page, size },
    })
    return res.data
  },
}
