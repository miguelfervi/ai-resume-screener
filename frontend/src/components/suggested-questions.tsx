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
    <div className="animate-fade-up mx-auto flex w-full flex-col gap-4 pt-2 pb-1 sm:max-w-xl sm:gap-5 sm:pt-6 sm:pb-2">
      <div className="text-left sm:text-center">
        <p className="font-heading text-foreground text-[1.65rem] leading-tight tracking-tight sm:text-3xl md:text-4xl">
          Screen resumes with questions
        </p>
        <p className="text-muted-foreground mt-2 max-w-md text-sm leading-relaxed sm:mx-auto sm:mt-3">
          Answers stay grounded in the indexed CV set — pick a prompt or write your
          own.
        </p>
      </div>

      <ul className="flex flex-col gap-2">
        {SUGGESTED_QUESTIONS.map((q, i) => (
          <li
            key={q}
            className="animate-fade-up"
            style={{ animationDelay: `${80 + i * 60}ms` }}
          >
            <button
              type="button"
              disabled={disabled}
              onClick={() => onSelect(q)}
              className="border-border/80 bg-card/80 active:bg-card focus-visible:ring-ring flex min-h-12 w-full items-start gap-3 rounded-xl border px-3.5 py-3 text-left text-sm transition-colors duration-150 focus-visible:ring-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 sm:min-h-0 sm:items-center sm:px-4 sm:py-3.5 [@media(hover:hover)]:hover:border-primary/35 [@media(hover:hover)]:hover:bg-card"
            >
              <span className="text-muted-foreground mt-0.5 font-mono text-[0.7rem] tabular-nums sm:mt-0">
                0{i + 1}
              </span>
              <span className="text-foreground leading-snug">{q}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
