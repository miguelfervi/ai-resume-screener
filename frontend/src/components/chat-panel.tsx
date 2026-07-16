import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react'
import { ArrowUp } from 'lucide-react'

import { CvPreviewPanel } from '@/components/cv-preview-panel'
import { MessageBubble } from '@/components/message-bubble'
import { SourceBadges } from '@/components/source-badges'
import { SuggestedQuestions } from '@/components/suggested-questions'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useChat } from '@/hooks/use-chat'
import { cn } from '@/lib/utils'
import type { Source } from '@/types/api'

type SelectedCv = {
  file: string
  candidateName: string
}

const PREVIEW_WIDTH_KEY = 'cv-preview-width'
const PREVIEW_MIN = 320
const PREVIEW_MAX_RATIO = 0.72
const PREVIEW_DEFAULT = 480

function clampPreviewWidth(width: number, viewport = window.innerWidth) {
  const max = Math.max(PREVIEW_MIN, Math.floor(viewport * PREVIEW_MAX_RATIO))
  return Math.min(max, Math.max(PREVIEW_MIN, Math.round(width)))
}

function readStoredPreviewWidth(): number {
  try {
    const raw = localStorage.getItem(PREVIEW_WIDTH_KEY)
    const n = raw ? Number(raw) : NaN
    if (Number.isFinite(n)) return clampPreviewWidth(n)
  } catch {
    /* ignore */
  }
  return clampPreviewWidth(PREVIEW_DEFAULT)
}

export function ChatPanel() {
  const { messages, loading, error, ask, clear } = useChat()
  const [draft, setDraft] = useState('')
  const [selectedCv, setSelectedCv] = useState<SelectedCv | null>(null)
  const [previewWidth, setPreviewWidth] = useState(PREVIEW_DEFAULT)
  const [resizing, setResizing] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const dragRef = useRef<{ startX: number; startWidth: number } | null>(null)

  useEffect(() => {
    setPreviewWidth(readStoredPreviewWidth())
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const onResizePointerMove = useCallback((e: PointerEvent) => {
    const drag = dragRef.current
    if (!drag) return
    const delta = drag.startX - e.clientX
    setPreviewWidth(clampPreviewWidth(drag.startWidth + delta))
  }, [])

  const stopResize = useCallback(() => {
    dragRef.current = null
    setResizing(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    window.removeEventListener('pointermove', onResizePointerMove)
    window.removeEventListener('pointerup', stopResize)
    window.removeEventListener('pointercancel', stopResize)
    setPreviewWidth((w) => {
      const next = clampPreviewWidth(w)
      try {
        localStorage.setItem(PREVIEW_WIDTH_KEY, String(next))
      } catch {
        /* ignore */
      }
      return next
    })
  }, [onResizePointerMove])

  useEffect(() => {
    function onWindowResize() {
      setPreviewWidth((w) => clampPreviewWidth(w))
    }
    window.addEventListener('resize', onWindowResize)
    return () => {
      window.removeEventListener('resize', onWindowResize)
      window.removeEventListener('pointermove', onResizePointerMove)
      window.removeEventListener('pointerup', stopResize)
      window.removeEventListener('pointercancel', stopResize)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [onResizePointerMove, stopResize])

  function startResize(e: ReactPointerEvent<HTMLDivElement>) {
    e.preventDefault()
    dragRef.current = { startX: e.clientX, startWidth: previewWidth }
    setResizing(true)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('pointermove', onResizePointerMove)
    window.addEventListener('pointerup', stopResize)
    window.addEventListener('pointercancel', stopResize)
  }

  async function submit(text = draft) {
    const next = text.trim()
    if (!next || loading) return
    setDraft('')
    await ask(next)
    if (window.matchMedia('(pointer: fine)').matches) {
      inputRef.current?.focus()
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit()
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      if (window.matchMedia('(pointer: fine)').matches) {
        e.preventDefault()
        void submit()
      }
    }
  }

  function onSelectSource(source: Source) {
    setSelectedCv({
      file: source.file,
      candidateName: source.candidateName,
    })
  }

  function onClearChat() {
    setSelectedCv(null)
    clear()
  }

  const empty = messages.length === 0 && !loading
  const previewOpen = selectedCv !== null

  return (
    <div className="chat-shell flex h-dvh max-h-dvh w-full overflow-hidden">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
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
              onClick={onClearChat}
              className="h-10 shrink-0 px-3 text-xs sm:h-8 sm:text-sm"
            >
              New chat
            </Button>
          ) : null}
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-3 sm:px-6 sm:py-5">
          <div
            className={cn(
              'flex w-full flex-col gap-3 sm:gap-4',
              previewOpen ? 'max-w-xl' : 'mx-auto max-w-2xl',
            )}
          >
            {empty ? (
              <SuggestedQuestions
                disabled={loading}
                onSelect={(q) => void submit(q)}
              />
            ) : null}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg}>
                {msg.role === 'assistant' && msg.sources?.length ? (
                  <SourceBadges
                    sources={msg.sources}
                    selectedFile={selectedCv?.file}
                    onSelectSource={onSelectSource}
                  />
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
          <div
            className={cn(
              'border-border/80 bg-card flex w-full items-end gap-2 rounded-2xl border p-1.5 shadow-sm sm:p-2',
              previewOpen ? 'max-w-xl' : 'mx-auto max-w-2xl',
            )}
          >
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
            Enter to send · Click a source to open the CV · Drag the edge to resize
          </p>
        </form>
      </div>

      {previewOpen && selectedCv ? (
        <>
          {/* Mobile: full-screen sheet */}
          <div className="animate-fade-up fixed inset-0 z-40 flex flex-col lg:hidden">
            <button
              type="button"
              className="bg-foreground/25 absolute inset-0"
              aria-label="Dismiss CV preview"
              onClick={() => setSelectedCv(null)}
            />
            <CvPreviewPanel
              file={selectedCv.file}
              candidateName={selectedCv.candidateName}
              onClose={() => setSelectedCv(null)}
              className="relative z-10 mt-10 h-[calc(100dvh-2.5rem)] rounded-t-2xl shadow-xl"
            />
          </div>

          {/* Desktop: resizable side panel */}
          <div
            className="animate-fade-up relative hidden h-full shrink-0 self-stretch lg:flex"
            style={{ width: previewWidth }}
          >
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize CV panel"
              aria-valuemin={PREVIEW_MIN}
              aria-valuemax={Math.floor(
                typeof window !== 'undefined'
                  ? window.innerWidth * PREVIEW_MAX_RATIO
                  : 900,
              )}
              aria-valuenow={previewWidth}
              tabIndex={0}
              onPointerDown={startResize}
              onKeyDown={(e) => {
                if (e.key === 'ArrowLeft') {
                  e.preventDefault()
                  setPreviewWidth((w) => {
                    const next = clampPreviewWidth(w + 24)
                    try {
                      localStorage.setItem(PREVIEW_WIDTH_KEY, String(next))
                    } catch {
                      /* ignore */
                    }
                    return next
                  })
                }
                if (e.key === 'ArrowRight') {
                  e.preventDefault()
                  setPreviewWidth((w) => {
                    const next = clampPreviewWidth(w - 24)
                    try {
                      localStorage.setItem(PREVIEW_WIDTH_KEY, String(next))
                    } catch {
                      /* ignore */
                    }
                    return next
                  })
                }
              }}
              className={cn(
                'group absolute top-0 bottom-0 -left-1 z-20 w-2 cursor-col-resize touch-none',
                'hover:bg-primary/15 active:bg-primary/25',
                resizing && 'bg-primary/25',
              )}
            >
              <span className="bg-border group-hover:bg-primary/50 absolute top-1/2 left-1/2 h-10 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full" />
            </div>
            <CvPreviewPanel
              file={selectedCv.file}
              candidateName={selectedCv.candidateName}
              onClose={() => setSelectedCv(null)}
              className={cn('h-full w-full', resizing && 'pointer-events-none')}
            />
          </div>
        </>
      ) : null}
    </div>
  )
}
