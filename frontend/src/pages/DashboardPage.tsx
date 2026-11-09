import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Hourglass, MessageSquareText } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { getApiErrorMessage, getMatters, getUserDashboard } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import { CountUp } from '../components/CountUp'
import { MattersTimeline } from '../components/MattersTimeline'
import { useAuth } from '../context/AuthContext'
import type { DeadlineClock, MattersResponse, UserDashboard } from '../types'

const mono = 'font-mono text-[10.5px] uppercase tracking-[0.14em]'

const fmt = (iso: string) =>
  new Date(iso + 'T00:00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

function Clock({ c, i }: { c: DeadlineClock; i: number }) {
  const reduce = useReducedMotion()
  const navigate = useNavigate()
  let pct = 0
  if (c.starts && c.due) {
    const total = new Date(c.due).getTime() - new Date(c.starts).getTime()
    pct = Math.min(100, Math.max(2, ((Date.now() - new Date(c.starts).getTime()) / total) * 100))
  }
  const left = c.days_left
  const passed = left !== null && left < 0
  const urgent = left !== null && left >= 0 && left <= 14
  return (
    <div className="grid grid-cols-1 items-center gap-x-5 gap-y-2 rounded-2xl border border-line bg-surface p-4 sm:grid-cols-[minmax(0,1fr)_170px]">
      <div className="min-w-0">
        <div className="text-[14.5px] font-semibold">{c.title}</div>
        <div className="mt-0.5 font-mono text-[11.5px] text-brass-light">{c.rule}</div>
        <button
          onClick={() => navigate(`/chat?c=${c.conversation_id}`)}
          className="mt-1 max-w-full truncate text-left text-[12.5px] text-muted hover:text-ink"
        >
          From: {c.question}
        </button>
      </div>
      <div className={`font-mono text-[11px] leading-relaxed sm:text-right ${passed || urgent ? 'text-warn-text' : 'text-muted'}`}>
        {c.due ? (
          <>
            {passed ? 'DUE ' : 'ACT BY '}
            {fmt(c.due).toUpperCase()}
            <br />
            {passed ? 'MAY HAVE PASSED' : `${left} DAY${left === 1 ? '' : 'S'} LEFT`}
          </>
        ) : (
          <>
            NOT STARTED
            <br />
            ASK AGAIN WITH THE DATE
          </>
        )}
      </div>
      <div className="col-span-full h-1 overflow-hidden rounded-full bg-fg/10">
        <motion.span
          className="block h-full rounded-full bg-gradient-to-r from-success-text via-brass to-warn-text"
          initial={reduce ? false : { width: 0 }}
          animate={{ width: `${c.due ? (passed ? 100 : pct) : 0}%` }}
          transition={{ delay: 0.1 + 0.08 * i, duration: 0.9, ease: [0.2, 0.8, 0.2, 1] }}
        />
      </div>
      {passed && (
        <div className="col-span-full text-[12px] text-warn-text">
          Talk to an advocate soon: some courts and forums can accept a late case if the delay is explained.
        </div>
      )}
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [data, setData] = useState<UserDashboard | null>(null)
  const [matters, setMatters] = useState<MattersResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    Promise.all([getUserDashboard(), getMatters()])
      .then(([d, m]) => {
        setData(d)
        setMatters(m)
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  // The login flow never collects a real name: "friend" for OTP users, "Guest" for guest login.
  const firstName = user?.phone ? 'friend' : 'Guest'

  if (loading) return <LoadingState label="Loading your matters…" />
  if (error || !data || !matters) return <ErrorState message={error ?? 'Could not load your matters.'} onRetry={load} />

  const upcoming = data.upcoming

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-10">
      <div className="mx-auto flex max-w-[1080px] flex-col gap-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end">
          <div className="flex-1">
            <div className={`${mono} text-brass-light`}>§ My matters</div>
            <h1 className="mt-2 font-display text-[32px] font-semibold leading-tight tracking-[-0.01em] md:text-[40px]">
              Namaste, <span className="italic text-brass-light">{firstName}</span>
            </h1>
            <div className="mt-1 max-w-[60ch] text-sm text-muted">
              Your questions sit on the line by when the incident happened. The law that applies depends on that date.
            </div>
          </div>
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex w-fit items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-[13px] font-bold text-primary-foreground shadow-card transition-colors hover:bg-primary-hover"
          >
            <MessageSquareText className="size-4" />
            Ask Nya-AI
          </button>
        </div>

        <dl className="fx-stagger grid grid-cols-1 border-y border-fg/15 sm:grid-cols-3">
          {[
            { v: <CountUp value={data.questions_answered} />, l: 'Questions answered free' },
            {
              v: <CountUp value={data.consults_booked} />,
              l: upcoming ? `Consult · ${upcoming.day_label}` : 'Consults booked',
            },
            { v: <CountUp value={data.saved_amount} prefix="₹" locale="en-IN" />, l: 'Saved on lawyer fees' },
          ].map((f, i) => (
            <div key={f.l} className={`px-4 py-5 ${i ? 'border-t border-line sm:border-l sm:border-t-0' : ''}`}>
              <dd className="m-0 font-display text-[38px] font-semibold leading-none tabular-nums md:text-[44px]">{f.v}</dd>
              <dt className={`${mono} mt-2 text-muted`}>{f.l}</dt>
            </div>
          ))}
        </dl>

        <section className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="font-display text-[24px] font-semibold">Timeline of incidents</h2>
            <span className="rounded-full border border-line px-2.5 py-1 font-mono text-[10.5px] tracking-[0.1em] text-muted">
              {matters.matters.length} QUESTION{matters.matters.length === 1 ? '' : 'S'}
            </span>
          </div>
          {matters.matters.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-6 text-sm text-muted">
              No questions yet. Ask Nya-AI something and add when it happened: it lands on this line, on the IPC side or
              the BNS side of 1 July 2024.
            </div>
          ) : (
            <MattersTimeline matters={matters.matters} />
          )}
        </section>

        <section className="flex flex-col gap-3">
          <div>
            <h2 className="flex items-center gap-2 font-display text-[24px] font-semibold">
              <Hourglass className="size-5 text-brass-light" />
              Clocks running
            </h2>
            <div className="mt-1 max-w-[66ch] text-[13.5px] text-muted">
              Time limits that may apply to your matters, counted from the incident date you gave. Nya-AI flags them; an
              advocate confirms the exact date for your case.
            </div>
          </div>
          {matters.clocks.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line p-5 text-sm text-muted">
              No time limits found in your questions yet. Cheque bounces, consumer complaints, RTI appeals and money
              claims start a clock here.
            </div>
          ) : (
            <div className="fx-stagger flex flex-col gap-2.5">
              {matters.clocks.map((c, i) => (
                <Clock key={`${c.conversation_id}-${c.title}`} c={c} i={i} />
              ))}
            </div>
          )}
          <div className="text-[12px] text-faint">Legal information, not legal advice.</div>
        </section>

        <section className="flex flex-col gap-3 pb-6">
          <h2 className="font-display text-[24px] font-semibold">Next consultation</h2>
          {upcoming ? (
            <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-dashed border-brass/45 p-5">
              <div
                className="flex size-[52px] flex-none items-center justify-center rounded-full text-[17px] font-bold text-white"
                style={{ background: upcoming.lawyer.avatar_color }}
              >
                {upcoming.lawyer.initials}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[15px] font-bold">{upcoming.lawyer.name}</div>
                <div className="mt-0.5 text-[13px] text-muted">
                  {upcoming.day_label} · {upcoming.slot_label} · {upcoming.consult_type} · 30 min
                </div>
              </div>
              <button
                onClick={() => navigate(`/call/${upcoming.id}`)}
                className="rounded-full bg-primary px-5 py-2.5 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover"
              >
                Open call room
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-dashed border-line p-5">
              <div className="min-w-0 flex-1">
                <div className="text-sm font-bold">No consultation booked</div>
                <div className="mt-0.5 text-[13px] text-body2">Ask Nya-AI first, it's free. Book an advocate only if you need one.</div>
              </div>
              <button
                onClick={() => navigate('/lawyers')}
                className="whitespace-nowrap rounded-full border border-line px-5 py-2.5 text-[13px] font-semibold text-ink transition-colors hover:border-brass/60"
              >
                See advocates
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
