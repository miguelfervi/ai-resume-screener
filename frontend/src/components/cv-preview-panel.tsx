import { useEffect } from 'react'
import { ExternalLink, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cvUrl } from '@/lib/api'
import { cn } from '@/lib/utils'

type CvPreviewPanelProps = {
  file: string
  candidateName: string
  onClose: () => void
  className?: string
}

export function CvPreviewPanel({
  file,
  candidateName,
  onClose,
  className,
}: CvPreviewPanelProps) {
  const url = cvUrl(file)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <aside
      className={cn(
        'bg-card border-border/60 flex h-full min-h-0 w-full flex-col overflow-hidden border-l',
        className,
      )}
      aria-label={`CV preview for ${candidateName}`}
    >
      <header className="border-border/60 safe-pt flex shrink-0 items-start justify-between gap-2 border-b px-3 py-3 sm:px-4">
        <div className="min-w-0">
          <p className="text-muted-foreground text-[0.6rem] font-medium tracking-[0.16em] uppercase">
            Resume
          </p>
          <h2 className="font-heading text-foreground truncate text-lg leading-tight tracking-tight sm:text-xl">
            {candidateName}
          </h2>
          <p className="text-muted-foreground truncate text-xs">{file}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button variant="ghost" size="icon" className="size-10 sm:size-8" asChild>
            <a href={url} target="_blank" rel="noreferrer" aria-label="Open PDF in new tab">
              <ExternalLink className="size-4" />
            </a>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-10 sm:size-8"
            onClick={onClose}
            aria-label="Close CV preview"
          >
            <X className="size-4" />
          </Button>
        </div>
      </header>

      <div className="relative min-h-0 flex-1 bg-neutral-200">
        <iframe
          key={url}
          src={url}
          title={`PDF — ${candidateName}`}
          className="absolute inset-0 h-full w-full border-0 bg-white"
        />
      </div>
    </aside>
  )
}
