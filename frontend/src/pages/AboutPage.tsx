import { Link } from 'react-router-dom'
import { Eyebrow, Panel } from '../components/InfoLayout'

const PRINCIPLES = [
  {
    tag: '01 · SOURCES',
    title: 'Only public law',
    text: 'Bare acts from India Code and reported Supreme Court judgments. No paid commentaries, no scraped textbooks.',
  },
  {
    tag: '02 · CITATIONS',
    title: 'Every claim has a section',
    text: 'If the library does not support an answer, Nya-AI says so instead of guessing. Each release is checked against a fixed set of test questions.',
  },
  {
    tag: '03 · PEOPLE',
    title: 'Advocates give the advice',
    text: "Each advocate's Bar Council enrolment is checked before they can take a booking. Fees are shown before you pay.",
  },
]

const TEAM = [
  { initials: 'SN', name: '[FOUNDER NAME]', role: 'Engineering' },
  { initials: 'LA', name: '[LEGAL ADVISOR]', role: 'Reviews policies and answers' },
  { initials: 'M', name: '[MENTOR]', role: 'Capstone guidance' },
]

export default function AboutPage() {
  return (
    <div className="flex flex-col gap-10">
      <section className="max-w-[760px]">
        <Eyebrow>ABOUT NYA-AI · न्याय</Eyebrow>
        <h1 className="mt-3 font-heading text-[32px] font-semibold leading-tight md:text-[44px]">
          Every citizen should be able to read the law that governs them.
        </h1>
        <p className="mt-4 text-[16px] leading-relaxed text-body2">
          India moved from the IPC, CrPC and Evidence Act to the BNS, BNSS and BSA in July 2024. Nya-AI explains the new
          codes in plain language, shows the exact section behind every sentence, and hands you to a verified advocate
          when you need advice on your own case.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/login" className="rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground hover:bg-primary-hover">
            Ask a question
          </Link>
          <Link to="/contact" className="rounded-full border border-line px-5 py-2.5 text-sm font-semibold text-ink hover:bg-soft">
            Join as an advocate
          </Link>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {PRINCIPLES.map((p) => (
          <Panel key={p.tag}>
            <div className="font-mono text-[11px] tracking-[0.12em] text-primary">{p.tag}</div>
            <h2 className="mt-2 font-heading text-xl font-semibold">{p.title}</h2>
            <p className="mt-2 text-[14.5px] leading-relaxed text-body2">{p.text}</p>
          </Panel>
        ))}
      </div>

      <section>
        <Eyebrow>THE TEAM</Eyebrow>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          {TEAM.map((t) => (
            <div key={t.initials} className="flex items-center gap-3 rounded-xl border border-line bg-surface/90 p-4">
              <div className="flex size-11 flex-none items-center justify-center rounded-full bg-gradient-to-br from-brass-light to-brass-dark font-bold text-navy-950">
                {t.initials}
              </div>
              <div>
                <div className="font-semibold">{t.name}</div>
                <div className="text-[13px] text-muted">{t.role}</div>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[14px] text-muted">
          Questions about Nya-AI? <Link to="/contact" className="text-primary hover:underline">Write to us</Link>.
        </p>
      </section>
    </div>
  )
}
