import api from './api'
import type { Vendor, Invoice } from '../types/ap.types'
import type { PaginatedResponse } from '../types/common.types'

export const apService = {
  async getVendors(page = 1, size = 20, search?: string): Promise<PaginatedResponse<Vendor>> {
    const res = await api.get<PaginatedResponse<Vendor>>('/ap/vendors', {
      params: { page, size, search },
    })
    return res.data
  },

  async getAllVendors(): Promise<Vendor[]> {
    const res = await api.get<PaginatedResponse<Vendor>>('/ap/vendors', {
      params: { page: 1, page_size: 200 },
    })
    return res.data.items
  },

  async getInvoices(page = 1, size = 20, status?: string): Promise<PaginatedResponse<Invoice>> {
    const res = await api.get<PaginatedResponse<Invoice>>('/ap/invoices', {
      params: { page, size, status },
    })
    return res.data
  },

  async createVendor(data: Record<string, unknown>): Promise<Vendor> {
    const res = await api.post<Vendor>('/ap/vendors', data)
    return res.data
  },

  async updateVendor(id: string, data: Record<string, unknown>): Promise<Vendor> {
    const res = await api.patch<Vendor>(`/ap/vendors/${id}`, data)
    return res.data
  },

  async createInvoice(data: Record<string, unknown>): Promise<Invoice> {
    const res = await api.post<Invoice>('/ap/invoices', data)
    return res.data
  },

  async updateInvoice(id: string, data: Record<string, unknown>): Promise<Invoice> {
    const res = await api.patch<Invoice>(`/ap/invoices/${id}`, data)
    return res.data
  },
}
