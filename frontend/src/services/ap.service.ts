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

  async getInvoices(page = 1, size = 20, status?: string): Promise<PaginatedResponse<Invoice>> {
    const res = await api.get<PaginatedResponse<Invoice>>('/ap/invoices', {
      params: { page, size, status },
    })
    return res.data
  },
}
