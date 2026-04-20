import { useEffect, useRef, useState } from 'react'
import { Plus, Send, Trash2, ChevronDown, ChevronRight, Bot, User, Zap, Database, Loader2, MessageSquare } from 'lucide-react'
import { llmService, Conversation, ConversationDetail, Message } from '../../../services/llm.service'

// ---------------------------------------------------------------------------
// SQL Results Table
// ---------------------------------------------------------------------------
function SqlResultTable({ sql_query, sql_results }: {
  sql_query: string | null | undefined
  sql_results: { columns: string[]; rows: Record<string, unknown>[]; row_count: number } | null | undefined
}) {
  const [open, setOpen] = useState(false)
  if (!sql_query) return null

  return (
    <div className="mt-3 rounded-lg overflow-hidden" style={{ border: '1px solid #2E4066' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 w-full px-3 py-2 text-[11px] font-medium text-left transition-colors"
        style={{ backgroundColor: '#1C2B4A', color: '#5BA4F5' }}
      >
        <Database className="h-3 w-3" />
        <span className="flex-1">SQL Query {sql_results ? `· ${sql_results.row_count} rows` : ''}</span>
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
      </button>
      {open && (
        <div>
          <pre className="px-3 py-2 text-[11px] overflow-x-auto" style={{ backgroundColor: '#111827', color: '#94A3B8', borderBottom: sql_results ? '1px solid #2E4066' : 'none' }}>
            {sql_query}
          </pre>
          {sql_results && sql_results.rows.length > 0 && (
            <div className="overflow-x-auto" style={{ backgroundColor: '#0F1826' }}>
              <table className="w-full text-[11px]">
                <thead>
                  <tr style={{ borderBottom: '1px solid #2E4066' }}>
                    {sql_results.columns.map(col => (
                      <th key={col} className="px-3 py-1.5 text-left font-semibold" style={{ color: '#64748B' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sql_results.rows.slice(0, 20).map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #1C2B4A' }}>
                      {sql_results.columns.map(col => (
                        <td key={col} className="px-3 py-1.5" style={{ color: '#94A3B8' }}>
                          {row[col] == null ? <span style={{ color: '#3A506B' }}>null</span> : String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {sql_results.rows.length > 20 && (
                <p className="px-3 py-1.5 text-[11px]" style={{ color: '#4A6080' }}>
                  Showing 20 of {sql_results.row_count} rows
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Message Bubble
// ---------------------------------------------------------------------------
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center mt-0.5" style={{ backgroundColor: '#0057AE' }}>
          <Bot className="h-4 w-4 text-white" />
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className="rounded-xl px-4 py-2.5 text-[13px] leading-relaxed"
          style={isUser
            ? { backgroundColor: '#0057AE', color: '#fff' }
            : { backgroundColor: '#1C2B4A', color: '#CBD5E1', border: '1px solid #2E4066' }
          }
        >
          {isUser
            ? <p>{msg.content}</p>
            : <p className="whitespace-pre-wrap">{msg.content}</p>
          }
        </div>
        {!isUser && (
          <SqlResultTable sql_query={msg.sql_query} sql_results={msg.sql_results} />
        )}
        <div className="flex items-center gap-2 px-1">
          <span className="text-[10px]" style={{ color: '#3A506B' }}>
            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {msg.latency_ms && (
            <span className="flex items-center gap-0.5 text-[10px]" style={{ color: '#3A506B' }}>
              <Zap className="h-2.5 w-2.5" />{msg.latency_ms}ms
            </span>
          )}
        </div>
      </div>
      {isUser && (
        <div className="flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center mt-0.5" style={{ backgroundColor: '#243558' }}>
          <User className="h-4 w-4" style={{ color: '#5BA4F5' }} />
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Example prompts shown on empty state
// ---------------------------------------------------------------------------
const EXAMPLE_PROMPTS = [
  "What is the total AP balance outstanding?",
  "Which employees have the highest attrition risk?",
  "Show me the top 5 vendors by invoice amount this year",
  "What is our budget vs actual spend by department?",
  "List all invoices flagged as duplicates",
  "Which expense reports are pending approval?",
]

// ---------------------------------------------------------------------------
// Main ChatPage
// ---------------------------------------------------------------------------
export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConv, setActiveConv] = useState<ConversationDetail | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConv?.messages])

  async function loadConversations() {
    try {
      const convs = await llmService.listConversations()
      setConversations(convs)
    } catch {
      // silently ignore — may not have API key yet
    }
  }

  async function openConversation(conv: Conversation) {
    setLoading(true)
    setError(null)
    try {
      const detail = await llmService.getConversation(conv.id)
      setActiveConv(detail)
    } catch {
      setError('Failed to load conversation')
    } finally {
      setLoading(false)
    }
  }

  async function newConversation() {
    try {
      const conv = await llmService.createConversation()
      setConversations(prev => [conv, ...prev])
      const detail = await llmService.getConversation(conv.id)
      setActiveConv(detail)
    } catch {
      setError('Failed to create conversation. Is ANTHROPIC_API_KEY configured?')
    }
  }

  async function deleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    await llmService.deleteConversation(id)
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeConv?.id === id) setActiveConv(null)
  }

  async function send(content?: string) {
    const text = (content ?? input).trim()
    if (!text || sending) return
    setInput('')
    setSending(true)
    setError(null)

    // Auto-create a conversation if none is active
    let conv = activeConv
    if (!conv) {
      try {
        const created = await llmService.createConversation()
        setConversations(prev => [created, ...prev])
        const detail = await llmService.getConversation(created.id)
        setActiveConv(detail)
        conv = detail
      } catch {
        setError('Failed to create conversation. Is ANTHROPIC_API_KEY configured?')
        setSending(false)
        return
      }
    }

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: 'temp-user',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setActiveConv(prev => prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : prev)

    try {
      const result = await llmService.sendMessage(conv.id, text)
      // Reload full conversation to get persisted messages
      const updated = await llmService.getConversation(conv.id)
      setActiveConv(updated)
      setConversations(prev =>
        prev.map(c => c.id === conv.id ? { ...c, title: updated.title, last_message_at: updated.last_message_at } : c)
      )
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Failed to send message')
      // Remove optimistic message
      setActiveConv(prev => prev ? { ...prev, messages: prev.messages.filter(m => m.id !== 'temp-user') } : prev)
    } finally {
      setSending(false)
      textareaRef.current?.focus()
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex h-[calc(100vh-56px)]" style={{ backgroundColor: '#0F1826' }}>

      {/* Sidebar */}
      <div className="w-64 flex flex-col flex-shrink-0" style={{ backgroundColor: '#1C2B4A', borderRight: '1px solid #243558' }}>
        <div className="p-3" style={{ borderBottom: '1px solid #243558' }}>
          <button
            onClick={newConversation}
            className="flex items-center gap-2 w-full rounded-lg px-3 py-2 text-[13px] font-medium transition-all"
            style={{ backgroundColor: '#0057AE', color: '#fff' }}
          >
            <Plus className="h-4 w-4" />
            New conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {conversations.length === 0 && (
            <p className="px-2 py-4 text-[12px] text-center" style={{ color: '#3A506B' }}>
              No conversations yet
            </p>
          )}
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => openConversation(conv)}
              className="group flex items-center gap-2 w-full rounded-lg px-2.5 py-2 text-left transition-all"
              style={{
                backgroundColor: activeConv?.id === conv.id ? '#243558' : 'transparent',
                color: activeConv?.id === conv.id ? '#CBD5E1' : '#64748B',
              }}
            >
              <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
              <span className="flex-1 truncate text-[12.5px]">{conv.title || 'Untitled'}</span>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded transition-opacity"
              >
                <Trash2 className="h-3 w-3" style={{ color: '#4A6080' }} />
              </button>
            </button>
          ))}
        </div>

        <div className="p-3" style={{ borderTop: '1px solid #243558' }}>
          <p className="text-[10px]" style={{ color: '#3A506B' }}>
            Powered by Claude · Phase 3 RAG+LLM
          </p>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-3.5" style={{ borderBottom: '1px solid #243558', backgroundColor: '#1C2B4A' }}>
          <Bot className="h-5 w-5" style={{ color: '#5BA4F5' }} />
          <div>
            <h1 className="text-[14px] font-semibold text-white">Finance Chat</h1>
            <p className="text-[11px]" style={{ color: '#4A6080' }}>Ask anything about your ERP data in plain English</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
          {loading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin" style={{ color: '#5BA4F5' }} />
            </div>
          )}

          {!loading && !activeConv && (
            <div className="flex flex-col items-center justify-center h-full gap-6 pb-8">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl" style={{ backgroundColor: '#0057AE' }}>
                <Bot className="h-7 w-7 text-white" />
              </div>
              <div className="text-center">
                <h2 className="text-[16px] font-semibold text-white mb-1">Finance Chat</h2>
                <p className="text-[13px]" style={{ color: '#4A6080' }}>
                  Start a conversation or pick an example below
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full max-w-xl">
                {EXAMPLE_PROMPTS.map(prompt => (
                  <button
                    key={prompt}
                    onClick={async () => {
                      const conv = await llmService.createConversation()
                      setConversations(prev => [conv, ...prev])
                      const detail = await llmService.getConversation(conv.id)
                      setActiveConv(detail)
                      setTimeout(() => send(prompt), 100)
                    }}
                    className="rounded-lg px-3 py-2.5 text-left text-[12px] transition-all"
                    style={{ backgroundColor: '#1C2B4A', color: '#94A3B8', border: '1px solid #2E4066' }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeConv?.messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}

          {sending && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center" style={{ backgroundColor: '#0057AE' }}>
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl" style={{ backgroundColor: '#1C2B4A', border: '1px solid #2E4066' }}>
                <Loader2 className="h-4 w-4 animate-spin" style={{ color: '#5BA4F5' }} />
                <span className="text-[13px]" style={{ color: '#64748B' }}>Thinking…</span>
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg px-4 py-3 text-[13px]" style={{ backgroundColor: '#2D1B1B', color: '#F87171', border: '1px solid #7F1D1D' }}>
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-3" style={{ borderTop: '1px solid #243558', backgroundColor: '#1C2B4A' }}>
          <div className="flex items-end gap-2 rounded-xl p-2" style={{ backgroundColor: '#0F1826', border: '1px solid #2E4066' }}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your financial data…"
              disabled={sending}
              rows={1}
              className="flex-1 resize-none bg-transparent px-2 py-1.5 text-[13px] outline-none placeholder:text-[#3A506B]"
              style={{ color: '#CBD5E1', maxHeight: 120 }}
              onInput={e => {
                const el = e.currentTarget
                el.style.height = 'auto'
                el.style.height = Math.min(el.scrollHeight, 120) + 'px'
              }}
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || sending}
              className="flex-shrink-0 h-8 w-8 rounded-lg flex items-center justify-center transition-all"
              style={{
                backgroundColor: input.trim() && !sending ? '#0057AE' : '#1C2B4A',
                color: input.trim() && !sending ? '#fff' : '#3A506B',
              }}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1.5 text-center text-[10px]" style={{ color: '#3A506B' }}>
            Press Enter to send · Shift+Enter for newline · Queries are read-only
          </p>
        </div>
      </div>
    </div>
  )
}
