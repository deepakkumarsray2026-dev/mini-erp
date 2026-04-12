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

  async getPurchaseOrders(page = 1, size = 20, status?: string): Promise<PaginatedResponse<PurchaseOrder>> {
    const res = await api.get<PaginatedResponse<PurchaseOrder>>('/procurement/orders', {
      params: { page, size, status },
    })
    return res.data
  },
}
