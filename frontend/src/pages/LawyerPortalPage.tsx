import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getApiErrorMessage, getLawyerDashboard, respondToBooking } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import ReviewQueue from '../components/ReviewQueue'
import { CountUp } from '../components/CountUp'
import type { Booking, LawyerDashboard } from '../types'

export default function LawyerPortalPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<LawyerDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [available, setAvailable] = useState(true)
  const [actingId, setActingId] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    getLawyerDashboard()
      .then(setData)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function respond(id: string, action: 'accept' | 'decline') {
    setActingId(id)
    try {
      const updated = await respondToBooking(id, action)
      setData((prev) =>
        prev ? { ...prev, requests: prev.requests.map((r) => (r.id === id ? updated : r)) } : prev,
      )
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setActingId(null)
    }
  }

  if (loading) return <LoadingState label="Loading portal…" />
  if (error && !data) return <ErrorState message={error} onRetry={load} />
  if (!data) return null

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <h1 className="font-heading text-2xl font-extrabold md:text-[28px]">Lawyer Portal</h1>
          <div className="mt-1 text-sm text-muted">
            Adv. Meera Krishnan · Criminal Law · Bar Council TN/1123/2014
          </div>
        </div>
        <button
          onClick={() => setAvailable((a) => !a)}
          className={`flex items-center gap-2 whitespace-nowrap rounded-full border px-[18px] py-2.5 text-[13px] font-bold ${
            available
              ? 'border-success-border bg-success-bg text-success-text'
              : 'border-line bg-bg text-muted'
          }`}
        >
          <span className={`h-2 w-2 rounded-full ${available ? 'fx-ping bg-success-text' : 'bg-faint'}`} />
          {available ? 'Available for consults' : 'Unavailable'}
        </button>
      </div>

      <div className="fx-stagger mt-5 grid max-w-[920px] grid-cols-2 gap-3.5 md:grid-cols-4">
        <div className="rounded-[18px] border border-line bg-surface p-[18px]">
          <div className="font-heading text-2xl font-extrabold text-success-text">
            <CountUp value={data.earnings_month} prefix="₹" />
          </div>
          <div className="mt-0.5 text-xs text-muted">earnings this month</div>
        </div>
        <div className="rounded-[18px] border border-line bg-surface p-[18px]">
          <div className="font-heading text-2xl font-extrabold"><CountUp value={data.consultations} /></div>
          <div className="mt-0.5 text-xs text-muted">consultations</div>
        </div>
        <div className="rounded-[18px] border border-line bg-surface p-[18px]">
          <div className="font-heading text-2xl font-extrabold">★ <CountUp value={data.rating} decimals={1} /></div>
          <div className="mt-0.5 text-xs text-muted">avg rating ({data.reviews} reviews)</div>
        </div>
        <div className="rounded-[18px] border border-line bg-surface p-[18px]">
          <div className="font-heading text-2xl font-extrabold"><CountUp value={data.share_pct} suffix="%" /></div>
          <div className="mt-0.5 text-xs text-muted">your share · payout every Friday</div>
        </div>
      </div>

      <ReviewQueue />

      <div className="mt-7 font-heading text-lg font-bold">Consultation requests</div>
      <div className="fx-stagger mt-3 flex max-w-[760px] flex-col gap-2.5">
        {data.requests.length === 0 && (
          <div className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
            No consultation requests yet.
          </div>
        )}
        {data.requests.map((r: Booking) => (
          <div
            key={r.id}
            className="flex items-center gap-3.5 rounded-[18px] border border-line bg-surface px-5 py-4"
          >
            <div className="flex h-[42px] w-[42px] flex-none items-center justify-center rounded-full bg-soft text-sm font-bold text-primary">
              {r.client_initials ?? '?'}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-bold">
                {r.client_name ?? 'Client'}
                {r.topic && <> · <span className="font-medium text-body2">{r.topic}</span></>}
              </div>
              <div className="mt-0.5 text-xs text-muted">
                {r.day_label} · {r.slot_label} · you receive ₹{r.lawyer_share}
              </div>
              {r.brief && (
                <details className="mt-1.5 text-[13px]">
                  <summary className="cursor-pointer font-mono text-[11px] tracking-[0.1em] text-primary">
                    CLIENT BRIEF · {r.brief.questions.length} QUESTION{r.brief.questions.length === 1 ? '' : 'S'}
                  </summary>
                  {r.brief.facts && <p className="mt-1.5 whitespace-pre-wrap text-body2">{r.brief.facts}</p>}
                  {r.brief.questions.length > 0 && (
                    <ol className="mt-1.5 list-decimal space-y-0.5 pl-5 text-body2">
                      {r.brief.questions.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ol>
                  )}
                </details>
              )}
            </div>
            {r.status === 'paid' || r.status === 'pending_payment' ? (
              <>
                <button
                  onClick={() => respond(r.id, 'accept')}
                  disabled={actingId === r.id}
                  className="rounded-full bg-success-text px-[18px] py-2.5 text-[13px] font-bold text-white disabled:opacity-60"
                >
                  Accept
                </button>
                <button
                  onClick={() => respond(r.id, 'decline')}
                  disabled={actingId === r.id}
                  className="rounded-full border border-line bg-surface px-[18px] py-2.5 text-[13px] font-semibold text-muted disabled:opacity-60"
                >
                  Decline
                </button>
              </>
            ) : (
              <>
                <div
                  className={`rounded-full px-3.5 py-1.5 text-xs font-bold ${
                    r.status === 'accepted'
                      ? 'bg-success-bg text-success-dark'
                      : 'bg-soft text-muted'
                  }`}
                >
                  {r.status === 'accepted' ? 'Accepted ✓' : 'Declined'}
                </div>
                {r.status === 'accepted' && (
                  <button
                    onClick={() => navigate('/messages')}
                    className="rounded-full bg-primary px-[18px] py-2.5 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover"
                  >
                    Respond
                  </button>
                )}
                {r.status === 'accepted' && (
                  <button
                    onClick={() => navigate(`/call/${r.id}`)}
                    className="rounded-full border border-primary/50 px-[18px] py-2.5 text-[13px] font-bold text-primary hover:bg-primary/10"
                  >
                    Call room
                  </button>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      <div className="mt-5 max-w-[760px] rounded-[18px] bg-soft px-5 py-4 text-[13px] leading-relaxed text-body2">
        <span className="font-bold text-ink">Next payout:</span> ₹9,800 on Friday, 17 Jul · UPI to
        meera@okaxis · AI pre-briefs each client so your consults start 60% faster.
      </div>
    </div>
  )
}
