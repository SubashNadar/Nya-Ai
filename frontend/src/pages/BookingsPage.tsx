import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getApiErrorMessage, getMyBookings } from '../lib/api'
import { EmptyState, ErrorState, LoadingState } from '../components/states'
import type { Booking, BookingStatus } from '../types'

const STATUS_LABEL: Record<BookingStatus, string> = {
  pending_payment: 'Payment pending',
  paid: 'Paid',
  accepted: 'Accepted',
  declined: 'Declined',
  completed: 'Completed',
}

const STATUS_CLASS: Record<BookingStatus, string> = {
  pending_payment: 'bg-warn-bg text-warn-text',
  paid: 'bg-soft text-primary',
  accepted: 'bg-success-bg text-success-dark',
  declined: 'bg-soft text-muted',
  completed: 'bg-soft text-muted',
}

// Same card layout as DashboardPage's upcoming-consultation card (lawyer avatar/initials/color,
// name, day/slot/consult-type labels), plus status/ref/fee since this screen lists every booking
// the user has rather than just the next one.
function ConsultationCard({ booking }: { booking: Booking }) {
  const navigate = useNavigate()
  const open = booking.status === 'paid' || booking.status === 'accepted'
  return (
    <div className="flex max-w-[640px] flex-wrap items-center gap-4 rounded-[20px] border border-line bg-surface p-5">
      <div
        className="flex h-[52px] w-[52px] flex-none items-center justify-center rounded-full text-[17px] font-bold text-white"
        style={{ background: booking.lawyer.avatar_color }}
      >
        {booking.lawyer.initials}
      </div>
      <div className="min-w-[160px] flex-1">
        <div className="text-[15px] font-bold">{booking.lawyer.name}</div>
        <div className="mt-0.5 text-[13px] text-muted">
          {booking.day_label} · {booking.slot_label} · {booking.consult_type} · 30 min
        </div>
        <div className="mt-1 text-xs text-faint">
          Ref {booking.ref} · ₹{booking.fee}
        </div>
      </div>
      <div
        className={`flex-none whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-bold ${STATUS_CLASS[booking.status]}`}
      >
        {STATUS_LABEL[booking.status]}
      </div>
      {open && (
        <button
          onClick={() => navigate(`/call/${booking.id}`)}
          className="w-full rounded-full bg-primary px-4 py-2 text-[13px] font-bold sm:w-auto sm:flex-none text-primary-foreground hover:bg-primary-hover"
        >
          Call room
        </button>
      )}
    </div>
  )
}

export default function BookingsPage() {
  const navigate = useNavigate()
  const [bookings, setBookings] = useState<Booking[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    getMyBookings()
      .then(({ bookings: b }) => setBookings(b))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <LoadingState label="Loading your consultations…" />
  if (error || !bookings) {
    return <ErrorState message={error ?? 'Could not load your consultations.'} onRetry={load} />
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <h1 className="font-heading text-2xl font-extrabold md:text-[28px]">My Consultations</h1>

      {bookings.length === 0 ? (
        <div className="mt-3 max-w-[640px]">
          <EmptyState
            title="No consultations yet"
            description="Ask Nya-AI first — it's free. Book a lawyer only if you need one."
            actionLabel="Ask Nya-AI"
            onAction={() => navigate('/chat')}
          />
        </div>
      ) : (
        <div className="fx-stagger mt-3 flex flex-col gap-3">
          {bookings.map((b) => (
            <ConsultationCard key={b.id} booking={b} />
          ))}
        </div>
      )}
    </div>
  )
}
