import { useState } from 'react'

import { ApiError, sendChat } from '@/lib/api'
import type { ChatMessage, RunMetrics, Source } from '@/types/api'

export type UiMessage = ChatMessage & {
  id: string
  sources?: Source[]
  metrics?: RunMetrics
}

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function useChat() {
  const [messages, setMessages] = useState<UiMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function ask(question: string) {
    const trimmed = question.trim()
    if (!trimmed || loading) return

    setError(null)

    const userMsg: UiMessage = {
      id: newId(),
      role: 'user',
      content: trimmed,
    }

    const history: ChatMessage[] = messages.map(({ role, content }) => ({
      role,
      content,
    }))

    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await sendChat({ question: trimmed, history })
      const assistantMsg: UiMessage = {
        id: newId(),
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        metrics: res.metrics,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Something went wrong'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  function clear() {
    setMessages([])
    setError(null)
  }

  return {
    messages,
    loading,
    error,
    ask,
    clear,
  }
}
