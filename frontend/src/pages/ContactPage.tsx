import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Eyebrow, Panel } from '../components/InfoLayout'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage, sendSupportMessage } from '../lib/api'
import type { SupportTopic } from '../types'

const TOPICS: { value: SupportTopic; label: string }[] = [
  { value: 'booking', label: 'Booking or payment' },
  { value: 'answer', label: 'Wrong or unclear answer' },
  { value: 'privacy', label: 'Privacy or data' },
  { value: 'advocate', label: 'Advocate partnership' },
  { value: 'other', label: 'Something else' },
]

const field =
  'w-full rounded-lg border border-line bg-navy-950/60 px-3 py-2.5 text-[15px] text-ink placeholder:text-faint focus:border-primary focus:outline-none'

export default function ContactPage() {
  const { user } = useAuth()
  const [topic, setTopic] = useState<SupportTopic>('booking')
  const [name, setName] = useState(user?.name ?? '')
  const [contact, setContact] = useState(user?.phone ? `+91 ${user.phone}` : '')
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [sentRef, setSentRef] = useState<string | null>(null)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setSending(true)
    try {
      const out = await sendSupportMessage({ name, contact, topic, text })
      setSentRef(out.ref)
      setText('')
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
      <Panel>
        <Eyebrow>CONTACT US · REPLY WITHIN 1 WORKING DAY</Eyebrow>
        <h1 className="mt-2 font-heading text-[28px] font-semibold md:text-[34px]">How can we help?</h1>

        {sentRef ? (
          <div role="status" className="mt-5 rounded-xl border border-success-border bg-success-bg p-4 text-success-text">
            <div className="font-semibold">Message sent.</div>
            <div className="mt-1 text-[14px]">
              Your reference is <span className="font-mono">{sentRef}</span>. We reply on the email or phone you gave.
            </div>
            <button onClick={() => setSentRef(null)} className="mt-3 text-[13px] font-semibold underline-offset-2 hover:underline">
              Send another message
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-5 flex flex-col gap-4">
            <fieldset>
              <legend className="mb-2 text-[13px] font-semibold text-body2">Topic</legend>
              <div className="flex flex-wrap gap-2">
                {TOPICS.map((t) => (
                  <label
                    key={t.value}
                    className={`cursor-pointer rounded-full border px-3.5 py-1.5 text-[13.5px] transition-colors ${
                      topic === t.value ? 'border-primary bg-primary/15 text-primary' : 'border-line text-body2 hover:border-focus'
                    }`}
                  >
                    <input
                      type="radio"
                      name="topic"
                      value={t.value}
                      checked={topic === t.value}
                      onChange={() => setTopic(t.value)}
                      className="sr-only"
                    />
                    {t.label}
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-1.5 text-[13px] font-semibold text-body2">
                Name
                <input required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} className={field} autoComplete="name" />
              </label>
              <label className="flex flex-col gap-1.5 text-[13px] font-semibold text-body2">
                Email or phone
                <input required minLength={3} maxLength={120} value={contact} onChange={(e) => setContact(e.target.value)} className={field} autoComplete="email" />
              </label>
            </div>
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold text-body2">
              Message
              <textarea
                required
                minLength={10}
                maxLength={2000}
                rows={5}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="For a booking, include the booking reference (NX-…)."
                className={field}
              />
            </label>
            <p className="text-[12.5px] text-muted">
              We use these details only to reply. See our{' '}
              <Link to="/legal#privacy" className="text-primary hover:underline">
                privacy notice
              </Link>
              .
            </p>
            <button
              type="submit"
              disabled={sending}
              className="self-start rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-primary-foreground hover:bg-primary-hover disabled:opacity-60"
            >
              {sending ? 'Sending…' : 'Send message'}
            </button>
          </form>
        )}
      </Panel>

      <div className="flex flex-col gap-4">
        <Panel>
          <div className="font-mono text-[11px] tracking-[0.12em] text-primary">REACH US</div>
          <dl className="mt-3 grid grid-cols-[80px_1fr] gap-y-2 text-[14px]">
            <dt className="font-mono text-[11px] tracking-[0.1em] text-faint">EMAIL</dt>
            <dd className="font-mono">[SUPPORT EMAIL]</dd>
            <dt className="font-mono text-[11px] tracking-[0.1em] text-faint">PHONE</dt>
            <dd className="font-mono">[SUPPORT PHONE]</dd>
            <dt className="font-mono text-[11px] tracking-[0.1em] text-faint">HOURS</dt>
            <dd>Mon–Sat · 09:00–19:00 IST</dd>
            <dt className="font-mono text-[11px] tracking-[0.1em] text-faint">ADDRESS</dt>
            <dd>[REGISTERED ADDRESS]</dd>
          </dl>
        </Panel>
        <Panel>
          <div className="font-mono text-[11px] tracking-[0.12em] text-primary">GRIEVANCE OFFICER · DPDP ACT</div>
          <div className="mt-2 font-semibold">[OFFICER NAME]</div>
          <div className="text-[13px] text-muted">[GRIEVANCE EMAIL] · reply within 7 days</div>
        </Panel>
        <section className="rounded-2xl border border-[#E5484D]/45 bg-surface/90 p-5">
          <div className="font-semibold">In danger right now?</div>
          <p className="mt-1 text-[14px] text-body2">
            Call <strong className="font-mono text-ink">112</strong>. Women's helpline: <strong className="font-mono text-ink">181</strong>. This inbox is
            not monitored for emergencies.
          </p>
        </section>
        <Link to="/help" className="text-[14px] text-primary hover:underline">
          Try quick answers in Help first
        </Link>
      </div>
    </div>
  )
}
