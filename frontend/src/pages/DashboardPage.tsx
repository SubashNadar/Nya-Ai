import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarCheck, MessageSquareText, PiggyBank } from 'lucide-react'
import { getApiErrorMessage, getUserDashboard } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import { useAuth } from '../context/AuthContext'
import type { UserDashboard } from '../types'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [data, setData] = useState<UserDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    getUserDashboard()
      .then(setData)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  // Demo behavior (template.html: userFirst = s.phone ? 'friend' : 'Guest') — the login flow never
  // collects a real name, so this is always "friend" for phone/OTP users and "Guest" for guest login,
  // not derived from user.name.
  const firstName = user?.phone ? 'friend' : 'Guest'

  if (loading) return <LoadingState label="Loading your dashboard…" />
  if (error || !data) return <ErrorState message={error ?? 'Could not load dashboard.'} onRetry={load} />

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <div className="relative max-w-[1000px] overflow-hidden rounded-3xl bg-gradient-to-br from-navy-800 via-navy-900 to-navy-950 p-7 text-white shadow-lift md:p-9">
        <div aria-hidden className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-brass/25 blur-3xl" />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.07)_1px,transparent_0)] [background-size:20px_20px]"
        />
        <div className="relative flex flex-col gap-5 md:flex-row md:items-end">
          <div className="flex-1">
            <h1 className="font-display text-[32px] font-semibold leading-tight tracking-[-0.01em] md:text-[40px]">
              Namaste, <span className="italic text-brass-light">{firstName}</span>
            </h1>
            <div className="mt-2 text-sm text-white/65">Your legal matters, all in one place</div>
          </div>
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex w-fit items-center gap-2 rounded-full bg-gradient-to-b from-brass-light to-brass px-5 py-2.5 text-[13px] font-bold text-navy-950 shadow-card transition-transform hover:-translate-y-0.5"
          >
            <MessageSquareText className="size-4" />
            Ask Nya-AI
          </button>
        </div>
      </div>

      <div className="mt-5 grid max-w-[1000px] grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-line bg-surface p-5 shadow-card transition-shadow hover:shadow-lift">
          <div className="mb-2.5 flex size-9 items-center justify-center rounded-xl bg-soft text-primary">
            <MessageSquareText className="size-[18px]" />
          </div>
          <div className="font-heading text-[26px] font-extrabold">{data.questions_answered}</div>
          <div className="mt-0.5 text-xs text-muted">questions answered free</div>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-5 shadow-card transition-shadow hover:shadow-lift">
          <div className="mb-2.5 flex size-9 items-center justify-center rounded-xl bg-soft text-primary">
            <CalendarCheck className="size-[18px]" />
          </div>
          <div className="font-heading text-[26px] font-extrabold">{data.consults_booked}</div>
          <div className="mt-0.5 text-xs text-muted">lawyer consults booked</div>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-5 shadow-card transition-shadow hover:shadow-lift">
          <div className="mb-2.5 flex size-9 items-center justify-center rounded-xl bg-success-bg text-success-text">
            <PiggyBank className="size-[18px]" />
          </div>
          <div className="font-heading text-[26px] font-extrabold text-success-text">
            ₹{data.saved_amount.toLocaleString('en-IN')}
          </div>
          <div className="mt-0.5 text-xs text-muted">saved vs typical lawyer fees</div>
        </div>
      </div>

      <div className="mt-9 font-display text-[22px] font-semibold">Upcoming consultation</div>
      {data.upcoming ? (
        <div className="mt-3 flex max-w-[1000px] items-center gap-4 rounded-[20px] border border-line bg-surface p-5">
          <div
            className="flex h-[52px] w-[52px] flex-none items-center justify-center rounded-full text-[17px] font-bold text-white"
            style={{ background: data.upcoming.lawyer.avatar_color }}
          >
            {data.upcoming.lawyer.initials}
          </div>
          <div className="flex-1">
            <div className="text-[15px] font-bold">{data.upcoming.lawyer.name}</div>
            <div className="mt-0.5 text-[13px] text-muted">
              {data.upcoming.day_label} · {data.upcoming.slot_label} · {data.upcoming.consult_type} · 30 min
            </div>
          </div>
          <button className="rounded-full bg-success-text px-5 py-2.5 text-[13px] font-bold text-white">
            Join call
          </button>
        </div>
      ) : (
        <div className="mt-3 flex max-w-[1000px] items-center gap-4 rounded-2xl border border-dashed border-focus bg-soft/60 p-5">
          <div className="flex-1">
            <div className="text-sm font-bold">No consultations yet</div>
            <div className="mt-0.5 text-[13px] text-body2">
              Ask Nya-AI first — it's free. Book a lawyer only if you need one.
            </div>
          </div>
          <button
            onClick={() => navigate('/chat')}
            className="whitespace-nowrap rounded-full bg-primary px-5 py-2.5 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover"
          >
            Ask Nya-AI
          </button>
        </div>
      )}

      <div className="mt-9 font-display text-[22px] font-semibold">Recent questions</div>
      <div className="mt-3 flex max-w-[1000px] flex-col gap-2">
        {data.recent_questions.map((rq, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-2xl border border-line bg-surface px-[18px] py-3.5 shadow-card transition-colors hover:border-focus"
          >
            <div className="flex size-8 flex-none items-center justify-center rounded-lg bg-soft text-primary">
              <MessageSquareText className="size-4" />
            </div>
            <div className="flex-1 text-sm font-medium">{rq.q}</div>
            <div className="whitespace-nowrap text-xs text-faint">{rq.when}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
