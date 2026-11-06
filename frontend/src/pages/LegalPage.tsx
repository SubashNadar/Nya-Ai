import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Eyebrow, Panel } from '../components/InfoLayout'

const SECTIONS = [
  { id: 'disclaimer', label: '§1 Disclaimer' },
  { id: 'privacy', label: '§2 Privacy notice' },
  { id: 'terms', label: '§3 Terms of use' },
  { id: 'refunds', label: '§4 Consultations and refunds' },
  { id: 'cookies', label: '§5 Cookies' },
]

const DATA_ROWS = [
  ['Mobile number, name', 'Sign in, booking receipts', 'Until you delete the account'],
  ['Questions and chats', 'Answer you; improve answer quality only if you opt in', '90 days'],
  ['Documents you share', 'Share with your advocate for the call', '30 days after the call'],
  ['Payment reference', 'Refunds, tax records', 'As tax law requires'],
]

export default function LegalPage() {
  const { hash } = useLocation()
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView()
  }, [hash])

  return (
    <div className="grid gap-8 lg:grid-cols-[220px_1fr]">
      <aside className="lg:sticky lg:top-24 lg:self-start">
        <Eyebrow>POLICIES · v0.9 DRAFT</Eyebrow>
        <nav aria-label="Policy sections" className="mt-3 flex gap-2 overflow-x-auto lg:flex-col lg:gap-1">
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="whitespace-nowrap rounded-md px-3 py-2 text-[13.5px] text-body2 hover:bg-soft hover:text-ink"
            >
              {s.label}
            </a>
          ))}
        </nav>
        <p className="mt-4 rounded-lg border border-warn-border bg-warn-bg p-3 text-[12.5px] leading-relaxed text-warn-text">
          Draft text for the prototype. A practising advocate must review it before launch.
        </p>
      </aside>

      <div className="flex min-w-0 flex-col gap-6">
        <Panel>
          <div id="disclaimer" className="scroll-mt-24 font-mono text-[11px] tracking-[0.12em] text-faint">§1 · LAST UPDATED 29.10.2026</div>
          <h1 className="mt-2 font-heading text-[28px] font-semibold md:text-[34px]">Legal information, not legal advice</h1>
          <div className="mt-4 space-y-3 text-[15px] leading-relaxed text-body2">
            <p>
              Nya-AI explains Indian bare acts and reported judgments in plain language, with a citation for every
              statement. It does not give advice on your specific matter.
            </p>
            <p>
              Using Nya-AI does not create an advocate and client relationship. That begins only when you book and hold
              a call with an enrolled advocate.
            </p>
            <p>
              Answers may be incomplete or out of date. Always check the cited section on India Code, and talk to an
              advocate before acting.
            </p>
            <p className="rounded-lg border border-[#E5484D]/45 p-3 text-ink">
              In an emergency, call <strong className="font-mono">112</strong>. Nya-AI cannot reach police, courts or
              anyone else for you.
            </p>
          </div>
        </Panel>

        <Panel>
          <h2 id="privacy" className="scroll-mt-24 font-heading text-2xl font-semibold">§2 Privacy notice, in short</h2>
          <div className="mt-1 font-mono text-[11px] tracking-[0.12em] text-faint">DIGITAL PERSONAL DATA PROTECTION ACT, 2023</div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-[14px]">
              <thead className="font-mono text-[11px] tracking-[0.12em] text-faint">
                <tr className="border-b border-line">
                  <th className="py-2 pr-4 font-normal">DATA</th>
                  <th className="py-2 pr-4 font-normal">WHY</th>
                  <th className="py-2 font-normal">KEPT FOR</th>
                </tr>
              </thead>
              <tbody>
                {DATA_ROWS.map(([d, why, kept]) => (
                  <tr key={d} className="border-b border-line/60 align-top">
                    <td className="py-2.5 pr-4 font-semibold">{d}</td>
                    <td className="py-2.5 pr-4 text-body2">{why}</td>
                    <td className="py-2.5 text-body2">{kept}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-[14.5px] leading-relaxed text-body2">
            We never sell your data or use it for advertising. Card and UPI details stay with the payment gateway
            (Razorpay). Calls are not recorded unless both sides agree.
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <div className="font-mono text-[11px] tracking-[0.12em] text-primary">YOUR RIGHTS</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-[14px] text-body2">
                <li>See a summary of the data we hold</li>
                <li>Correct or erase it</li>
                <li>Withdraw consent at any time</li>
                <li>Name someone to act for you</li>
                <li>Complain to our grievance officer, then to the Data Protection Board of India</li>
              </ul>
              <p className="mt-3 text-[13.5px] text-muted">
                To use any of these rights, <Link to="/contact" className="text-primary underline-offset-2 hover:underline">write to us</Link> with the topic “Privacy or data”.
              </p>
            </div>
            <div className="rounded-xl border border-line bg-navy-950/50 p-4">
              <div className="font-mono text-[11px] tracking-[0.12em] text-primary">GRIEVANCE OFFICER</div>
              <div className="mt-2 font-semibold">[OFFICER NAME]</div>
              <div className="font-mono text-[13px] text-body2">[GRIEVANCE EMAIL]</div>
              <div className="mt-1 text-[13px] text-muted">Reply within 7 days</div>
            </div>
          </div>
        </Panel>

        <Panel>
          <h2 id="terms" className="scroll-mt-24 font-heading text-2xl font-semibold">§3 Terms of use</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-[14.5px] leading-relaxed text-body2">
            <li>You must be 18 or older, or use Nya-AI with a parent or guardian.</li>
            <li>Do not use Nya-AI to harass anyone, or to draft anything meant to mislead a court or authority.</li>
            <li>Answers quote public law from India Code and reported judgments. Nya-AI does not copy paid commentaries or textbooks.</li>
            <li>Advocates are independent professionals. Nya-AI checks their enrolment but is not party to the advice they give.</li>
          </ul>
        </Panel>

        <Panel>
          <h2 id="refunds" className="scroll-mt-24 font-heading text-2xl font-semibold">§4 Consultations and refunds</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-[14.5px] leading-relaxed text-body2">
            <li>The fee is shown before you pay. The advocate receives 70% of it.</li>
            <li>Full refund if the advocate cancels, or does not join within 10 minutes of the start time.</li>
            <li>Cancel up to 2 hours before the call for a full refund. After that, 50% is refunded.</li>
            <li>Refunds go back to the original payment method, usually within 5 to 7 working days.</li>
          </ul>
        </Panel>

        <Panel>
          <h2 id="cookies" className="scroll-mt-24 font-heading text-2xl font-semibold">§5 Cookies</h2>
          <p className="mt-3 text-[14.5px] leading-relaxed text-body2">
            Nya-AI uses only what it needs to keep you signed in: a sign-in token stored in your browser. There are no
            advertising or analytics cookies today. If analytics are added later, they will be off until you agree.
          </p>
        </Panel>
      </div>
    </div>
  )
}
