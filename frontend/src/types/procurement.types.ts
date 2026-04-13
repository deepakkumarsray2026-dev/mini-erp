export interface Requisition {
  id: string
  pr_number: string
  requester_id: string
  requester_name: string | null
  title: string
  description: string | null
  total_amount: number
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'converted' | 'cancelled'
  required_date: string | null
  created_at: string
}

export interface PurchaseOrder {
  id: string
  po_number: string
  vendor_id: string
  vendor_name: string | null
  requisition_id: string | null
  issued_date: string
  expected_delivery: string | null
  total_amount: number
  status: 'draft' | 'sent' | 'acknowledged' | 'partially_received' | 'received' | 'cancelled'
  created_at: string
}
