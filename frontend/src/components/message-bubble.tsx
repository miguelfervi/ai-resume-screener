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
      className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}
    >
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground',
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none [&_p]:my-1 [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5 [&_pre]:my-2 [&_code]:rounded [&_code]:bg-background/60 [&_code]:px-1 [&_code]:py-0.5">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {children ? <div className="mt-2">{children}</div> : null}
      </div>
    </div>
  )
}
