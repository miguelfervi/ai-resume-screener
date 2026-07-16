import { SUGGESTED_QUESTIONS } from '@/lib/api'

type SuggestedQuestionsProps = {
  onSelect: (question: string) => void
  disabled?: boolean
}

export function SuggestedQuestions({
  onSelect,
  disabled = false,
}: SuggestedQuestionsProps) {
  return (
    <div className="animate-fade-up mx-auto flex w-full flex-col gap-5 pt-3 pb-2 sm:max-w-xl sm:gap-6 sm:pt-8">
      <div className="text-left sm:text-center">
        <p className="font-heading text-foreground text-[1.7rem] leading-[1.15] tracking-tight sm:text-3xl md:text-4xl">
          Ask the résumé set
        </p>
        <p className="text-muted-foreground mt-2.5 max-w-md text-sm leading-relaxed sm:mx-auto sm:mt-3">
          Answers are grounded in the indexed CVs only — no guessing when evidence
          is weak.
        </p>
        <p className="text-primary/80 mt-3 text-[0.65rem] font-medium tracking-[0.16em] uppercase sm:mt-4">
          Sample questions from the brief
        </p>
      </div>

      <ul className="flex flex-col gap-2">
        {SUGGESTED_QUESTIONS.map((q, i) => (
          <li
            key={q}
            className="animate-fade-up"
            style={{ animationDelay: `${80 + i * 70}ms` }}
          >
            <button
              type="button"
              disabled={disabled}
              onClick={() => onSelect(q)}
              className="border-border/80 bg-card/85 active:bg-card focus-visible:ring-ring group flex min-h-12 w-full items-start gap-3 rounded-xl border px-3.5 py-3 text-left text-sm shadow-sm transition-[border-color,background-color,transform] duration-150 focus-visible:ring-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 sm:min-h-0 sm:items-center sm:px-4 sm:py-3.5 [@media(hover:hover)]:hover:border-primary/40 [@media(hover:hover)]:hover:bg-card [@media(hover:hover)]:hover:-translate-y-px"
            >
              <span className="text-muted-foreground mt-0.5 font-mono text-[0.7rem] tabular-nums sm:mt-0">
                0{i + 1}
              </span>
              <span className="text-foreground flex-1 leading-snug">{q}</span>
              <span className="text-muted-foreground mt-0.5 hidden text-[0.65rem] tracking-wide uppercase opacity-0 transition-opacity group-hover:opacity-100 sm:mt-0 sm:inline">
                Ask
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
