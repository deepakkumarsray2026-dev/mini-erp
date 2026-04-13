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

  async getAllDepartments(): Promise<Department[]> {
    const res = await api.get<PaginatedResponse<Department>>('/workforce/departments', {
      params: { page: 1, page_size: 200, active_only: true },
    })
    return res.data.items
  },

  async getAllJobs(): Promise<{ id: string; title: string; code: string }[]> {
    const res = await api.get<{ id: string; title: string; code: string }[]>('/workforce/jobs')
    return res.data
  },

  async createDepartment(data: Record<string, unknown>): Promise<Department> {
    const res = await api.post<Department>('/workforce/departments', data)
    return res.data
  },

  async updateDepartment(id: string, data: Record<string, unknown>): Promise<Department> {
    const res = await api.patch<Department>(`/workforce/departments/${id}`, data)
    return res.data
  },

  async createEmployee(data: Record<string, unknown>): Promise<Employee> {
    const res = await api.post<Employee>('/workforce/employees', data)
    return res.data
  },

  async updateEmployee(id: string, data: Record<string, unknown>): Promise<Employee> {
    const res = await api.patch<Employee>(`/workforce/employees/${id}`, data)
    return res.data
  },
}
