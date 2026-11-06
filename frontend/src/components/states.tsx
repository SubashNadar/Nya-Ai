export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-muted">
      <div className="flex gap-1.5">
        <span className="h-2 w-2 animate-dotpulse rounded-full bg-primary [animation-delay:0s]" />
        <span className="h-2 w-2 animate-dotpulse rounded-full bg-primary [animation-delay:0.15s]" />
        <span className="h-2 w-2 animate-dotpulse rounded-full bg-primary [animation-delay:0.3s]" />
      </div>
      <div className="text-sm font-medium">{label}</div>
      <div aria-hidden className="mt-2 flex w-full max-w-[320px] flex-col gap-2">
        <div className="fx-skeleton fx-skeleton-row w-full" />
        <div className="fx-skeleton fx-skeleton-row w-4/5" />
        <div className="fx-skeleton fx-skeleton-row w-3/5" />
      </div>
    </div>
  )
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-center">
      <div className="max-w-sm text-sm font-medium text-warn-text">{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary-hover"
        >
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <div className="flex items-center gap-4 rounded-[20px] bg-soft p-5">
      <div className="flex-1">
        <div className="text-sm font-bold text-ink">{title}</div>
        {description && <div className="mt-0.5 text-[13px] text-body2">{description}</div>}
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="whitespace-nowrap rounded-full bg-primary px-5 py-2.5 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
