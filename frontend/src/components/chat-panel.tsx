import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'

import { MessageBubble } from '@/components/message-bubble'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useChat } from '@/hooks/use-chat'

export function ChatPanel() {
  const { messages, loading, error, ask, clear } = useChat()
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function submit() {
    const text = draft.trim()
    if (!text || loading) return
    setDraft('')
    await ask(text)
    inputRef.current?.focus()
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit()
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submit()
    }
  }

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h1 className="text-base font-semibold tracking-tight">
            AI Resume Screener
          </h1>
          <p className="text-muted-foreground text-xs">
            Ask questions about the CV collection
          </p>
        </div>
        {messages.length > 0 ? (
          <Button type="button" variant="ghost" size="sm" onClick={clear}>
            Clear
          </Button>
        ) : null}
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto flex max-w-2xl flex-col gap-3">
          {messages.length === 0 && !loading ? (
            <p className="text-muted-foreground py-12 text-center text-sm">
              Ask about skills, education, or a candidate profile.
            </p>
          ) : null}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading ? (
            <p className="text-muted-foreground text-sm">Thinking…</p>
          ) : null}

          {error ? (
            <p
              className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          <div ref={bottomRef} />
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="border-t bg-background px-4 py-3"
      >
        <div className="mx-auto flex max-w-2xl gap-2">
          <Textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask a question…"
            rows={1}
            disabled={loading}
            className="min-h-10 max-h-32 resize-none"
            aria-label="Chat question"
          />
          <Button
            type="submit"
            disabled={loading || !draft.trim()}
            className="self-end"
          >
            Send
          </Button>
        </div>
      </form>
    </div>
  )
}
