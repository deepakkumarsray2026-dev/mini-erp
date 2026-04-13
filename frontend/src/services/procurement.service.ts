import api from './api'
import type { Requisition, PurchaseOrder } from '../types/procurement.types'
import type { PaginatedResponse } from '../types/common.types'

export const procurementService = {
  async getRequisitions(page = 1, size = 20, status?: string): Promise<PaginatedResponse<Requisition>> {
    const res = await api.get<PaginatedResponse<Requisition>>('/procurement/requisitions', {
      params: { page, size, status },
    })
    return res.data
  },

  async createRequisition(data: Record<string, unknown>): Promise<Requisition> {
    const res = await api.post<Requisition>('/procurement/requisitions', data)
    return res.data
  },

  async updateRequisition(id: string, data: Record<string, unknown>): Promise<Requisition> {
    const res = await api.patch<Requisition>(`/procurement/requisitions/${id}`, data)
    return res.data
  },

  async getPurchaseOrders(page = 1, size = 20, status?: string): Promise<PaginatedResponse<PurchaseOrder>> {
    const res = await api.get<PaginatedResponse<PurchaseOrder>>('/procurement/orders', {
      params: { page, size, status },
    })
    return res.data
  },

  async createPurchaseOrder(data: Record<string, unknown>): Promise<PurchaseOrder> {
    const res = await api.post<PurchaseOrder>('/procurement/orders', data)
    return res.data
  },

  async updatePurchaseOrder(id: string, data: Record<string, unknown>): Promise<PurchaseOrder> {
    const res = await api.patch<PurchaseOrder>(`/procurement/orders/${id}`, data)
    return res.data
  },
}
