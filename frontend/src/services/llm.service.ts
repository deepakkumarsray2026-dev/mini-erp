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
}
