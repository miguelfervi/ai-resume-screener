import { useEffect, useState } from 'react'
import { FileText } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Source } from '@/types/api'

type SourceBadgesProps = {
  sources: Source[]
  selectedFile?: string | null
  onSelectSource?: (source: Source) => void
}

export function SourceBadges({
  sources,
  selectedFile,
  onSelectSource,
}: SourceBadgesProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  // Closing the CV clears selection; drop local highlight/snippet with it.
  useEffect(() => {
    if (!selectedFile) setOpenId(null)
  }, [selectedFile])

  if (!sources.length) return null

  return (
    <div className="border-border/60 flex flex-col gap-2 border-t pt-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-muted-foreground text-[0.65rem] font-medium tracking-[0.14em] uppercase">
          Sources
        </p>
        <p className="text-muted-foreground hidden text-[0.65rem] sm:block">
          Click to open the CV
        </p>
      </div>
      <div className="flex flex-col gap-1.5 sm:flex-row sm:flex-wrap">
        {sources.map((source, i) => {
          const id = `${source.file}-${source.section}-${i}`
          const open = openId === id
          const selected = selectedFile === source.file
          return (
            <div key={id} className="w-full sm:w-auto sm:max-w-full">
              <button
                type="button"
                onClick={() => {
                  onSelectSource?.(source)
                  setOpenId(open ? null : id)
                }}
                className="focus-visible:ring-ring w-full rounded-md focus-visible:ring-2 focus-visible:outline-none sm:w-auto"
                aria-pressed={selected}
                title={`Open ${source.file}`}
              >
                <Badge
                  variant="outline"
                  className={cn(
                    'h-auto min-h-9 w-full max-w-full cursor-pointer justify-start gap-1.5 rounded-md px-2.5 py-2 text-left text-xs font-normal transition-colors sm:min-h-0 sm:w-auto sm:py-1',
                    selected &&
                      'border-primary/45 bg-accent text-accent-foreground shadow-sm',
                  )}
                >
                  <FileText className="text-muted-foreground size-3 shrink-0 opacity-70" />
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
