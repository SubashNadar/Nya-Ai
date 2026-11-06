import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PhoneOff, Video } from 'lucide-react'
import { EmptyState, ErrorState, LoadingState } from '../components/states'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage, getBooking } from '../lib/api'
import { AGENDA, CALL_MINUTES } from '../lib/plan'
import type { Booking } from '../types'

type Tab = 'agenda' | 'brief' | 'notes'

const mm = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`

function readNotes(key: string) {
  try {
    return localStorage.getItem(key) ?? ''
  } catch {
    return ''
  }
}

// The call room for one booking. Video is not wired to a calling provider yet, so the stage says
// how the call actually happens today; the agenda, brief and private notes all work.
export default function CallPage() {
  const { bookingId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [booking, setBooking] = useState<Booking | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('agenda')
  const [elapsed, setElapsed] = useState(0)
  const notesKey = `nya_ai_notes_${bookingId}`
  const [notes, setNotes] = useState(() => readNotes(notesKey))

  function load() {
    if (!bookingId) return
    setLoading(true)
    setError(null)
    getBooking(bookingId)
      .then(setBooking)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [bookingId])

  useEffect(() => {
    const started = Date.now()
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => clearInterval(t)
  }, [])

  function saveNotes(v: string) {
    setNotes(v)
    try {
      localStorage.setItem(notesKey, v)
    } catch {
      // notes stay in memory only
    }
  }

  const back = user?.role === 'lawyer' ? '/portal' : '/bookings'

  if (loading) return <LoadingState label="Opening the call room…" />
  if (error || !booking) return <ErrorState message={error ?? 'Booking not found.'} onRetry={load} />
  if (booking.status !== 'paid' && booking.status !== 'accepted') {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-[480px]">
          <EmptyState
            title="The call room is closed"
            description={
              booking.status === 'pending_payment'
                ? 'This consultation is not paid yet.'
                : 'This consultation is no longer active.'
            }
            actionLabel="Back to consultations"
            onAction={() => navigate(back)}
          />
        </div>
      </div>
    )
  }

  const isLawyer = user?.role === 'lawyer'
  const other = isLawyer
    ? { initials: booking.client_initials ?? '?', name: booking.client_name ?? 'Client', tag: 'CLIENT' }
    : { initials: booking.lawyer.initials, name: booking.lawyer.name, tag: 'BAR VERIFIED' }
  const minute = Math.floor(elapsed / 60)
  const over = elapsed >= CALL_MINUTES * 60

  return (
    <div className="flex flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
      <div className="flex min-w-0 flex-1 flex-col p-4 md:p-6">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <h1 className="font-heading text-xl font-semibold">Consultation · {booking.topic ?? booking.ref}</h1>
          <span className={`font-mono text-[12px] ${over ? 'text-warn-text' : 'text-primary'}`}>
            <span aria-hidden className="mr-1.5 inline-block size-2 rounded-full bg-[#E5484D] align-middle" />
            {mm(elapsed)} / {CALL_MINUTES}:00
          </span>
          <span className="font-mono text-[11px] tracking-[0.1em] text-faint">NOT RECORDED</span>
        </div>

        <div className="relative mt-4 flex min-h-[280px] flex-1 flex-col items-center justify-center rounded-2xl border border-line bg-navy-950/70 p-6 text-center">
          <div className="flex size-20 items-center justify-center rounded-full bg-gradient-to-br from-brass-light to-brass-dark text-2xl font-bold text-navy-950">
            {other.initials}
          </div>
          <div className="mt-3 font-semibold">{other.name}</div>
          <div className="font-mono text-[10.5px] tracking-[0.12em] text-success-text">{other.tag}</div>
          <div className="mt-5 flex max-w-[440px] items-start gap-2 rounded-lg border border-warn-border bg-warn-bg p-3 text-left text-[13px] text-warn-text">
            <Video className="mt-0.5 size-4 flex-none" />
            <span>
              In-app video is not connected yet. At the booked time ({booking.day_label}, {booking.slot_label}), the advocate calls the
              client's registered mobile. Keep this room open for the agenda, brief and notes.
            </span>
          </div>
          <div className="absolute bottom-3 right-3 hidden size-14 sm:flex items-center justify-center rounded-xl border border-line bg-surface text-sm font-bold text-primary">
            {user?.initials ?? 'You'}
          </div>
        </div>

        <div className="mt-4 flex justify-center">
          <button
            onClick={() => navigate(back)}
            className="flex items-center gap-2 rounded-full bg-[#E5484D] px-6 py-3 text-sm font-bold text-white hover:bg-[#d13a3f]"
          >
            <PhoneOff className="size-4" /> Leave call room
          </button>
        </div>
      </div>

      <aside className="flex w-full flex-col border-t border-line bg-surface/80 lg:w-[360px] lg:border-l lg:border-t-0">
        <div role="tablist" aria-label="Call panels" className="flex border-b border-line">
          {(['agenda', 'brief', 'notes'] as Tab[]).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={`flex-1 py-3 font-mono text-[11.5px] tracking-[0.12em] ${
                tab === t ? 'border-b-2 border-primary text-primary' : 'text-muted hover:text-ink'
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>
        <div role="tabpanel" className="flex-1 overflow-y-auto p-5">
          {tab === 'agenda' && (
            <ol className="flex flex-col gap-3">
              {AGENDA.map((a) => {
                const state = minute >= a.to ? 'done' : minute >= a.from ? 'now' : 'next'
                return (
                  <li key={a.label} className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 font-mono text-[13px] ${
                        state === 'done' ? 'text-success-text' : state === 'now' ? 'text-primary' : 'text-faint'
                      }`}
                    >
                      {state === 'done' ? '✓' : state === 'now' ? '●' : '○'}
                    </span>
                    <span className={`flex-1 text-[14.5px] ${state === 'next' ? 'text-muted' : ''}`}>{a.label}</span>
                    <span className="font-mono text-[11.5px] text-faint">
                      {String(a.from).padStart(2, '0')}–{String(a.to).padStart(2, '0')}
                    </span>
                  </li>
                )
              })}
            </ol>
          )}

          {tab === 'brief' &&
            (booking.brief ? (
              <div className="flex flex-col gap-4 text-[14.5px]">
                <div>
                  <div className="font-mono text-[11px] tracking-[0.12em] text-primary">FACTS</div>
                  <p className="mt-1 whitespace-pre-wrap leading-relaxed text-body2">{booking.brief.facts || 'Not given.'}</p>
                </div>
                {booking.brief.questions.length > 0 && (
                  <div>
                    <div className="font-mono text-[11px] tracking-[0.12em] text-primary">QUESTIONS</div>
                    <ol className="mt-1 list-decimal space-y-1 pl-5 text-body2">
                      {booking.brief.questions.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ol>
                  </div>
                )}
                {booking.brief.goals.length > 0 && (
                  <div>
                    <div className="font-mono text-[11px] tracking-[0.12em] text-primary">WANTS TO</div>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {booking.brief.goals.map((g) => (
                        <span key={g} className="rounded-full border border-line px-2.5 py-1 text-[12.5px] text-body2">
                          {g}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[14px] text-muted">No brief was written for this consultation.</p>
            ))}

          {tab === 'notes' && (
            <label className="flex h-full flex-col gap-2 text-[13px] text-muted">
              Private notes, kept only on this device.
              <textarea
                value={notes}
                onChange={(e) => saveNotes(e.target.value)}
                rows={12}
                placeholder="What was said, what to do next…"
                className="w-full flex-1 rounded-lg border border-line bg-navy-950/60 p-3 text-[14.5px] text-ink placeholder:text-faint focus:border-primary focus:outline-none"
              />
            </label>
          )}
        </div>
      </aside>
    </div>
  )
}
