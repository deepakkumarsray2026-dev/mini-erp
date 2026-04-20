import api from './api'

export interface Conversation {
  id: string
  title: string | null
  status: string
  created_at: string
  last_message_at: string | null
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sql_query?: string | null
  sql_results?: { columns: string[]; rows: Record<string, unknown>[]; row_count: number } | null
  input_tokens?: number | null
  output_tokens?: number | null
  latency_ms?: number | null
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export interface OcrJob {
  id: string
  document_type: string
  file_name: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  extracted_data: Record<string, unknown> | null
  error_message: string | null
  model_used: string | null
  input_tokens: number | null
  output_tokens: number | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export const llmService = {
  // Conversations
  createConversation: (): Promise<Conversation> =>
    api.post('/llmops/chat/conversations').then((r) => r.data),

  listConversations: (): Promise<Conversation[]> =>
    api.get('/llmops/chat/conversations').then((r) => r.data),

  getConversation: (id: string): Promise<ConversationDetail> =>
    api.get(`/llmops/chat/conversations/${id}`).then((r) => r.data),

  deleteConversation: (id: string): Promise<void> =>
    api.delete(`/llmops/chat/conversations/${id}`).then((r) => r.data),

  sendMessage: (convId: string, content: string) =>
    api.post(`/llmops/chat/conversations/${convId}/message`, { content }).then((r) => r.data as {
      message: Message
      sql_query: string | null
      sql_results: { columns: string[]; rows: Record<string, unknown>[]; row_count: number } | null
      latency_ms: number | null
    }),

  // Duplicate detection
  reindexInvoices: () =>
    api.post('/llmops/embeddings/reindex').then((r) => r.data),

  checkDuplicate: (invoiceId: string) =>
    api.post(`/llmops/invoices/${invoiceId}/duplicate-check`).then((r) => r.data),

  listDuplicates: (page = 1) =>
    api.get('/llmops/invoices/duplicates', { params: { page } }).then((r) => r.data),

  // OCR
  uploadForOcr: (file: File): Promise<OcrJob> => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/llmops/ocr/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  listOcrJobs: (page = 1): Promise<{ items: OcrJob[]; page: number; page_size: number }> =>
    api.get('/llmops/ocr/jobs', { params: { page } }).then((r) => r.data),

  getOcrJob: (jobId: string): Promise<OcrJob> =>
    api.get(`/llmops/ocr/jobs/${jobId}`).then((r) => r.data),
}
