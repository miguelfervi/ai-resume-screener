import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { ArrowUp } from 'lucide-react'

import { MessageBubble } from '@/components/message-bubble'
import { SourceBadges } from '@/components/source-badges'
import { SuggestedQuestions } from '@/components/suggested-questions'
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

  async function submit(text = draft) {
    const next = text.trim()
    if (!next || loading) return
    setDraft('')
    await ask(next)
    // avoid forcing keyboard open again on mobile after send
    if (window.matchMedia('(pointer: fine)').matches) {
      inputRef.current?.focus()
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit()
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Desktop: Enter sends. Mobile soft keyboards prefer explicit Send.
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      if (window.matchMedia('(pointer: fine)').matches) {
        e.preventDefault()
        void submit()
      }
    }
  }

  const empty = messages.length === 0 && !loading

  return (
    <div className="chat-shell flex h-dvh max-h-dvh flex-col overflow-hidden">
      <header className="border-border/60 bg-card/50 safe-pt flex shrink-0 items-center justify-between gap-3 border-b px-3 py-3 backdrop-blur-md sm:px-5 sm:py-4">
        <div className="min-w-0">
          <p className="text-muted-foreground text-[0.6rem] font-medium tracking-[0.16em] uppercase sm:text-[0.65rem] sm:tracking-[0.18em]">
            CV screening
          </p>
          <h1 className="font-heading text-foreground truncate text-xl leading-tight tracking-tight sm:mt-0.5 sm:text-2xl">
            Resume Screener
          </h1>
        </div>
        {messages.length > 0 ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={clear}
            className="h-10 shrink-0 px-3 text-xs sm:h-8 sm:text-sm"
          >
            New chat
          </Button>
        ) : null}
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-3 sm:px-6 sm:py-5">
        <div className="mx-auto flex w-full max-w-2xl flex-col gap-3 sm:gap-4">
          {empty ? (
            <SuggestedQuestions
              disabled={loading}
              onSelect={(q) => void submit(q)}
            />
          ) : null}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg}>
              {msg.role === 'assistant' && msg.sources?.length ? (
                <SourceBadges sources={msg.sources} />
              ) : null}
            </MessageBubble>
          ))}

          {loading ? (
            <div className="animate-fade-up text-muted-foreground flex items-center gap-2 px-1 text-sm">
              <span className="bg-primary animate-pulse-dot inline-block size-1.5 rounded-full" />
              <span className="bg-primary animate-pulse-dot inline-block size-1.5 rounded-full [animation-delay:140ms]" />
              <span className="bg-primary animate-pulse-dot inline-block size-1.5 rounded-full [animation-delay:280ms]" />
              <span className="ml-1">Retrieving from CVs…</span>
            </div>
          ) : null}

          {error ? (
            <p
              className="animate-fade-up border-destructive/25 bg-destructive/8 text-destructive rounded-xl border px-3 py-3 text-sm sm:px-4"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          <div ref={bottomRef} className="h-1" />
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="border-border/60 bg-card/70 safe-pb shrink-0 border-t px-3 pt-3 backdrop-blur-md sm:px-6 sm:pt-4"
      >
        <div className="border-border/80 bg-card mx-auto flex w-full max-w-2xl items-end gap-2 rounded-2xl border p-1.5 shadow-sm sm:p-2">
          <Textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about skills or a candidate…"
            rows={1}
            disabled={loading}
            enterKeyHint="send"
            className="max-h-32 min-h-11 flex-1 resize-none border-0 bg-transparent text-base shadow-none focus-visible:ring-0 sm:max-h-36 sm:text-sm"
            aria-label="Chat question"
          />
          <Button
            type="submit"
            size="icon"
            disabled={loading || !draft.trim()}
            className="size-11 shrink-0 rounded-xl sm:size-10"
            aria-label="Send"
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
        <p className="text-muted-foreground mx-auto mt-2 hidden max-w-2xl pb-1 text-center text-[0.7rem] sm:block">
          Enter to send · Shift+Enter for a new line
        </p>
      </form>
    </div>
  )
}
