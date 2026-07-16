import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'

import type { UiMessage } from '@/hooks/use-chat'
import { cn } from '@/lib/utils'

type MessageBubbleProps = {
  message: UiMessage
  children?: ReactNode
}

export function MessageBubble({ message, children }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'animate-fade-up flex w-full',
        isUser ? 'justify-end' : 'justify-start',
      )}
    >
      <div
        className={cn(
          'w-full max-w-[100%] px-3.5 py-2.5 text-[0.9375rem] leading-relaxed sm:max-w-[min(42rem,92%)] sm:px-4 sm:py-3 sm:text-sm',
          isUser
            ? 'bg-primary text-primary-foreground ml-6 rounded-2xl rounded-br-md shadow-sm sm:ml-12'
            : 'border-border/70 bg-card/90 text-foreground mr-4 rounded-2xl rounded-bl-md border shadow-sm backdrop-blur-sm sm:mr-12',
        )}
      >
        {!isUser ? (
          <p className="text-muted-foreground mb-1 text-[0.65rem] font-medium tracking-[0.14em] uppercase">
            Grounded answer
          </p>
        ) : null}

        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none break-words prose-headings:font-heading prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {children ? <div className="mt-2.5 sm:mt-3">{children}</div> : null}
      </div>
    </div>
  )
}
