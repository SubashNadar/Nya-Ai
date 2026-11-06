import { useEffect, useState } from 'react'
import { decideReview, getApiErrorMessage, getReviews } from '../lib/api'
import type { AnswerReview, ReviewDecision } from '../types'

/**
 * Lawyer portal: AI answers held for an advocate before the user sees them (live matters such as an
 * arrest or a court date). Approve, edit or reject; the decision goes back into the user's chat.
 * Uses the portal's existing card and button styles.
 */
export default function ReviewQueue() {
  const [reviews, setReviews] = useState<AnswerReview[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [actingId, setActingId] = useState<string | null>(null)
  const [editing, setEditing] = useState<{ id: string; mode: 'edit' | 'reject'; text: string } | null>(null)

  function load() {
    getReviews('pending')
      .then((r) => setReviews(r.reviews))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoaded(true))
  }

  useEffect(load, [])

  async function decide(review: AnswerReview, decision: ReviewDecision, text?: string) {
    setActingId(review.id)
    setError(null)
    try {
      await decideReview(review.id, {
        decision,
        ...(decision === 'edited' ? { text, points: [] } : {}),
        ...(decision === 'rejected' && text ? { note: text } : {}),
      })
      setReviews((prev) => prev.filter((r) => r.id !== review.id))
      setEditing(null)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setActingId(null)
    }
  }

  if (!loaded) return null

  return (
    <>
      <div className="mt-7 font-heading text-lg font-bold">Answers waiting for review</div>
      <div className="mt-1 text-[13px] text-muted">
        Live matters are held here. The client sees the answer only after you approve, edit or reject it.
      </div>
      {error && <div className="mt-2 max-w-[760px] text-[13px] text-warn-text">{error}</div>}
      <div className="fx-stagger mt-3 flex max-w-[760px] flex-col gap-2.5">
        {reviews.length === 0 && (
          <div className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
            No answers waiting for review.
          </div>
        )}
        {reviews.map((r) => {
          const draft = r.draft
          const busy = actingId === r.id
          const open = editing?.id === r.id ? editing : null
          return (
            <div key={r.id} className="rounded-[18px] border border-line bg-surface px-5 py-4">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[11px] tracking-[0.1em] text-muted">
                    QUESTION · {new Date(r.created_at).toLocaleString('en-IN')}
                  </div>
                  <div className="mt-1 text-sm font-bold">{r.question}</div>
                </div>
                {r.critique && (
                  <div className="whitespace-nowrap rounded-full bg-soft px-3.5 py-1.5 text-xs font-bold text-muted">
                    {r.critique.confidence_label} · {Math.round(r.critique.confidence * 100)}%
                  </div>
                )}
              </div>

              {draft && (
                <div className="mt-3 text-[13px] text-body2">
                  <div className="font-mono text-[11px] tracking-[0.1em] text-primary">DRAFT ANSWER</div>
                  <p className="mt-1 whitespace-pre-wrap">{draft.text}</p>
                  {draft.points.length > 0 && (
                    <ul className="mt-1.5 list-disc space-y-0.5 pl-5">
                      {draft.points.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  )}
                  {draft.citations.length > 0 && (
                    <div className="mt-1.5 font-mono text-[11px] text-muted">
                      Sources: {draft.citations.map((c) => `${c.act} §${c.section}`).join(', ')}
                    </div>
                  )}
                </div>
              )}

              {open && (
                <textarea
                  value={open.text}
                  onChange={(e) => setEditing({ ...open, text: e.target.value })}
                  rows={open.mode === 'edit' ? 5 : 2}
                  placeholder={open.mode === 'edit' ? 'The answer the client will see' : 'Note for the client (optional)'}
                  className="mt-3 w-full rounded-2xl border border-line bg-bg px-4 py-3 text-[13px] text-ink outline-none focus:border-primary"
                />
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                {open ? (
                  <>
                    <button
                      onClick={() => decide(r, open.mode === 'edit' ? 'edited' : 'rejected', open.text.trim())}
                      disabled={busy || (open.mode === 'edit' && !open.text.trim())}
                      className="rounded-full bg-primary px-[18px] py-2.5 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover disabled:opacity-60"
                    >
                      {open.mode === 'edit' ? 'Send edited answer' : 'Reject and send note'}
                    </button>
                    <button
                      onClick={() => setEditing(null)}
                      disabled={busy}
                      className="rounded-full border border-line bg-surface px-[18px] py-2.5 text-[13px] font-semibold text-muted disabled:opacity-60"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => decide(r, 'approved')}
                      disabled={busy}
                      className="rounded-full bg-success-text px-[18px] py-2.5 text-[13px] font-bold text-white disabled:opacity-60"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => setEditing({ id: r.id, mode: 'edit', text: draft?.text ?? '' })}
                      disabled={busy}
                      className="rounded-full border border-primary/50 px-[18px] py-2.5 text-[13px] font-bold text-primary hover:bg-primary/10 disabled:opacity-60"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setEditing({ id: r.id, mode: 'reject', text: '' })}
                      disabled={busy}
                      className="rounded-full border border-line bg-surface px-[18px] py-2.5 text-[13px] font-semibold text-muted disabled:opacity-60"
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
