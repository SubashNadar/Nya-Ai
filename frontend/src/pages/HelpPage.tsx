import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Eyebrow, Panel } from '../components/InfoLayout'

type Faq = { cat: string; q: string; a: string; link?: { to: string; label: string } }

const FAQS: Faq[] = [
  {
    cat: 'Bookings and refunds',
    q: 'The advocate did not join my call. Do I get a refund?',
    a: 'Yes. If the advocate is more than 10 minutes late, the full amount goes back to your original payment method within 5 to 7 working days. You can also rebook with another advocate at no extra cost.',
    link: { to: '/legal#refunds', label: 'Refund policy §4' },
  },
  {
    cat: 'Bookings and refunds',
    q: 'How do I cancel or reschedule a booking?',
    a: 'Write to us with your booking reference (NX-…). Cancel up to 2 hours before the call for a full refund; after that, 50% is refunded.',
    link: { to: '/contact', label: 'Contact us' },
  },
  {
    cat: 'Bookings and refunds',
    q: 'Payment failed but money was deducted',
    a: 'The booking stays unpaid and you can retry from the payment screen. If money left your account, the bank usually reverses it within 5 to 7 working days. Send us the booking reference if it does not come back.',
  },
  {
    cat: 'Understanding answers',
    q: 'Why does Nya-AI quote BNS instead of IPC?',
    a: 'The Bharatiya Nyaya Sanhita replaced the Indian Penal Code from 1 July 2024. For incidents before that date the IPC still applies. Enter the incident date in the chat side panel and Nya-AI shows which code governs.',
  },
  {
    cat: 'Understanding answers',
    q: 'Is the answer legal advice?',
    a: 'No. Nya-AI gives legal information with a citation for every statement. For advice on your own situation, book an advocate.',
    link: { to: '/legal#disclaimer', label: 'Disclaimer §1' },
  },
  {
    cat: 'Understanding answers',
    q: 'An answer looks wrong. What should I do?',
    a: 'Check the cited section on India Code, then tell us through the Contact page with the topic “Wrong or unclear answer”. Include the question you asked.',
    link: { to: '/contact', label: 'Report an answer' },
  },
  {
    cat: 'Account and sign-in',
    q: 'I did not get the OTP',
    a: 'Ask for a new code after a short wait, and check that the number is a 10-digit Indian mobile number. If it still does not arrive, write to us.',
  },
  {
    cat: 'Account and sign-in',
    q: 'How do I delete my account and data?',
    a: 'Write to us with the topic “Privacy or data”. We confirm the deletion within 7 days.',
    link: { to: '/legal#privacy', label: 'Privacy notice §2' },
  },
  {
    cat: 'For advocates',
    q: 'How do I join as an advocate?',
    a: 'Write to us with the topic “Advocate partnership” and your Bar Council enrolment number. We verify it before you can take bookings. You keep 70% of each consultation fee.',
    link: { to: '/contact', label: 'Apply' },
  },
]

const CATS = Array.from(new Set(FAQS.map((f) => f.cat)))

export default function HelpPage() {
  const [query, setQuery] = useState('')
  const [cat, setCat] = useState<string | null>(null)

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    return FAQS.filter((f) => (!cat || f.cat === cat) && (!q || `${f.q} ${f.a}`.toLowerCase().includes(q)))
  }, [query, cat])

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="flex min-w-0 flex-col gap-5">
        <div>
          <Eyebrow>QUICK SUPPORT</Eyebrow>
          <h1 className="mt-2 font-heading text-[28px] font-semibold md:text-[34px]">What do you need help with?</h1>
        </div>
        <label className="relative block">
          <span className="sr-only">Search help</span>
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-faint" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search help, e.g. refund"
            className="w-full rounded-xl border border-line bg-surface/90 py-3 pl-10 pr-4 text-[15px] text-ink placeholder:text-faint focus:border-primary focus:outline-none"
          />
        </label>
        <div className="flex flex-wrap gap-2">
          {CATS.map((c) => {
            const count = FAQS.filter((f) => f.cat === c).length
            const active = cat === c
            return (
              <button
                key={c}
                onClick={() => setCat(active ? null : c)}
                aria-pressed={active}
                className={`rounded-full border px-3.5 py-1.5 text-[13.5px] transition-colors ${
                  active ? 'border-primary bg-primary/15 text-primary' : 'border-line text-body2 hover:border-focus'
                }`}
              >
                {c} <span className="font-mono text-[11px] text-faint">· {count}</span>
              </button>
            )
          })}
        </div>
        <div className="font-mono text-[11px] tracking-[0.12em] text-faint" aria-live="polite">
          {results.length} {results.length === 1 ? 'RESULT' : 'RESULTS'}
        </div>
        <div className="flex flex-col gap-2">
          {results.map((f, i) => (
            <details key={f.q} open={i === 0} className="group rounded-xl border border-line bg-surface/90 px-4 py-3">
              <summary className="cursor-pointer list-none font-semibold marker:hidden">
                <span className="mr-2 font-mono text-primary group-open:hidden">+</span>
                <span className="mr-2 hidden font-mono text-primary group-open:inline">−</span>
                {f.q}
              </summary>
              <p className="mt-2 text-[14.5px] leading-relaxed text-body2">{f.a}</p>
              {f.link && (
                <Link to={f.link.to} className="mt-2 inline-block font-mono text-[12px] text-primary hover:underline">
                  {f.link.label} →
                </Link>
              )}
            </details>
          ))}
          {results.length === 0 && (
            <p className="text-[14px] text-muted">
              Nothing matches. <Link to="/contact" className="text-primary hover:underline">Write to us</Link> and a person will reply.
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <Panel>
          <div className="font-semibold">Still stuck?</div>
          <p className="mt-1 text-[14px] text-body2">A person, not the AI, replies within one working day.</p>
          <Link
            to="/contact"
            className="mt-3 inline-block rounded-full bg-primary px-5 py-2 text-sm font-bold text-primary-foreground hover:bg-primary-hover"
          >
            Message support
          </Link>
        </Panel>
        <section className="rounded-2xl border border-danger/45 bg-surface/90 p-5">
          <div className="font-semibold">Emergency</div>
          <p className="mt-1 text-[14px] text-body2">
            Police, fire, ambulance: <strong className="font-mono text-ink">112</strong>. Women's helpline:{' '}
            <strong className="font-mono text-ink">181</strong>.
          </p>
        </section>
      </div>
    </div>
  )
}
