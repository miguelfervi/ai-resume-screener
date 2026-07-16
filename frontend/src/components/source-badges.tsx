import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Source } from '@/types/api'

type SourceBadgesProps = {
  sources: Source[]
}

export function SourceBadges({ sources }: SourceBadgesProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  if (!sources.length) return null

  return (
    <div className="flex flex-col gap-2 border-t border-border/60 pt-2">
      <p className="text-[0.65rem] font-medium tracking-[0.14em] text-muted-foreground uppercase">
        Sources
      </p>
      <div className="flex flex-col gap-1.5 sm:flex-row sm:flex-wrap">
        {sources.map((source, i) => {
          const id = `${source.file}-${source.section}-${i}`
          const open = openId === id
          return (
            <div key={id} className="w-full sm:w-auto sm:max-w-full">
              <button
                type="button"
                onClick={() => setOpenId(open ? null : id)}
                className="focus-visible:ring-ring w-full rounded-md focus-visible:ring-2 focus-visible:outline-none sm:w-auto"
              >
                <Badge
                  variant="outline"
                  className={cn(
                    'h-auto min-h-9 w-full max-w-full cursor-pointer justify-start gap-1.5 rounded-md px-2.5 py-2 text-left text-xs font-normal transition-colors sm:min-h-0 sm:w-auto sm:py-1',
                    open && 'border-primary/40 bg-accent text-accent-foreground',
                  )}
                >
                  <span className="truncate font-medium">{source.candidateName}</span>
                  <span className="text-muted-foreground shrink-0">
                    · {source.section}
                  </span>
                  <span className="text-muted-foreground ml-auto shrink-0 tabular-nums sm:ml-0">
                    {Math.round(source.score * 100)}%
                  </span>
                </Badge>
              </button>
              {open ? (
                <p className="text-muted-foreground animate-fade-up mt-1.5 w-full text-xs leading-relaxed sm:max-w-sm">
                  <span className="text-foreground/70 font-medium">{source.file}</span>
                  {' — '}
                  {source.snippet}
                </p>
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
