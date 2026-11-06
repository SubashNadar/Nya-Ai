import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Plus, X } from 'lucide-react'
import { AGENDA, CALL_MINUTES, loadPlan, savePlan } from '../lib/plan'

const GOALS = ['Understand my options', 'Get a notice drafted', 'Recover money', 'Prepare for a hearing', 'Check a document']

const STEPS = ['PLAN', 'SCHEDULE', 'PAY', 'CALL']

const field =
  'w-full rounded-lg border border-line bg-navy-950/60 px-3 py-2.5 text-[15px] text-ink placeholder:text-faint focus:border-primary focus:outline-none'

export function StepBar({ current }: { current: number }) {
  return (
    <ol className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] tracking-[0.12em]" aria-label="Booking steps">
      {STEPS.map((s, i) => (
        <li key={s} className="flex items-center gap-2" aria-current={i === current ? 'step' : undefined}>
          <span className={i === current ? 'text-primary' : i < current ? 'text-success-text' : 'text-faint'}>
            {String(i + 1).padStart(2, '0')} {s}
          </span>
          {i < STEPS.length - 1 && <span className="text-faint">›</span>}
        </li>
      ))}
    </ol>
  )
}

function Num({ n }: { n: number }) {
  return (
    <span className="flex size-7 flex-none items-center justify-center rounded-full border border-primary/50 font-mono text-[12px] text-primary">
      {String(n).padStart(2, '0')}
    </span>
  )
}

export default function ConsultPlanPage() {
  const navigate = useNavigate()
  const fromChat = (useLocation().state as { question?: string } | null)?.question ?? ''
  const saved = loadPlan()

  const [topic, setTopic] = useState(saved?.topic ?? '')
  const [facts, setFacts] = useState(saved?.facts || fromChat)
  const [questions, setQuestions] = useState<string[]>(saved?.questions ?? [])
  const [draftQ, setDraftQ] = useState('')
  const [goals, setGoals] = useState<string[]>(saved?.goals ?? [])

  function addQuestion() {
    const q = draftQ.trim()
    if (!q || questions.length >= 10) return
    setQuestions([...questions, q])
    setDraftQ('')
  }

  function toggleGoal(g: string) {
    setGoals(goals.includes(g) ? goals.filter((x) => x !== g) : goals.length < 5 ? [...goals, g] : goals)
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    savePlan({ topic: topic.trim(), facts: facts.trim(), questions, goals })
    navigate('/lawyers')
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <StepBar current={0} />
      <h1 className="mt-3 font-heading text-2xl font-semibold md:text-[30px]">Plan your discussion with an advocate</h1>
      <p className="mt-1 max-w-[640px] text-[14px] text-muted">
        A clear brief lets the advocate spend the {CALL_MINUTES} minutes on your options, not on catching up. Only the
        advocate you book can see it.
      </p>

      <form onSubmit={submit} className="mt-6 grid max-w-[1080px] gap-6 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-5">
          <section className="rounded-2xl border border-line bg-surface/90 p-5">
            <label className="flex items-center gap-3 font-semibold">
              <Num n={1} />
              In a few words, what is this about?
            </label>
            <input
              required
              maxLength={200}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Deposit not returned"
              className={`${field} mt-3`}
            />
          </section>

          <section className="rounded-2xl border border-line bg-surface/90 p-5">
            <label htmlFor="plan-facts" className="flex items-center gap-3 font-semibold">
              <Num n={2} />
              Facts summary
              {fromChat && <span className="font-mono text-[10.5px] tracking-[0.12em] text-faint">FROM YOUR CHAT · EDITABLE</span>}
            </label>
            <textarea
              id="plan-facts"
              rows={4}
              maxLength={4000}
              value={facts}
              onChange={(e) => setFacts(e.target.value)}
              placeholder="What happened, when, and who is involved. Dates and amounts help."
              className={`${field} mt-3`}
            />
          </section>

          <section className="rounded-2xl border border-line bg-surface/90 p-5">
            <div className="flex items-center gap-3 font-semibold">
              <Num n={3} />
              Questions to ask
            </div>
            {questions.length > 0 && (
              <ol className="mt-3 flex flex-col gap-2">
                {questions.map((q, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-lg border border-line bg-navy-950/40 px-3 py-2 text-[14.5px]">
                    <span className="font-mono text-[12px] text-primary">Q{i + 1}</span>
                    <span className="flex-1">{q}</span>
                    <button
                      type="button"
                      onClick={() => setQuestions(questions.filter((_, j) => j !== i))}
                      aria-label={`Remove question ${i + 1}`}
                      className="text-faint hover:text-ink"
                    >
                      <X className="size-4" />
                    </button>
                  </li>
                ))}
              </ol>
            )}
            <div className="mt-3 flex gap-2">
              <input
                value={draftQ}
                onChange={(e) => setDraftQ(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addQuestion()
                  }
                }}
                maxLength={300}
                placeholder="Add a question"
                aria-label="Add a question"
                className={field}
              />
              <button
                type="button"
                onClick={addQuestion}
                disabled={!draftQ.trim() || questions.length >= 10}
                className="flex flex-none items-center gap-1 rounded-lg border border-primary/50 px-3 text-[13px] font-semibold text-primary hover:bg-primary/10 disabled:opacity-50"
              >
                <Plus className="size-4" /> Add
              </button>
            </div>
          </section>

          <section className="rounded-2xl border border-line bg-surface/90 p-5">
            <fieldset>
              <legend className="flex items-center gap-3 font-semibold">
                <Num n={4} />
                What you want out of it
              </legend>
              <div className="mt-3 flex flex-wrap gap-2">
                {GOALS.map((g) => {
                  const on = goals.includes(g)
                  return (
                    <button
                      key={g}
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggleGoal(g)}
                      className={`rounded-full border px-3.5 py-1.5 text-[13.5px] transition-colors ${
                        on ? 'border-primary bg-primary/15 text-primary' : 'border-line text-body2 hover:border-focus'
                      }`}
                    >
                      {on ? '✓ ' : ''}
                      {g}
                    </button>
                  )
                })}
              </div>
            </fieldset>
          </section>

          <p className="text-[13px] text-muted">
            Keep documents ready to show on the call. Uploading them here is not available yet.
          </p>
        </div>

        <aside className="flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start">
          <section className="rounded-2xl border border-line bg-surface/90 p-5">
            <div className="font-mono text-[11px] tracking-[0.12em] text-primary">SUGGESTED AGENDA · {CALL_MINUTES} MIN</div>
            <ol className="mt-3 flex flex-col gap-2.5">
              {AGENDA.map((a) => (
                <li key={a.label} className="grid grid-cols-[52px_1fr] gap-2 text-[14px]">
                  <span className="font-mono text-[12px] text-faint">
                    {String(a.from).padStart(2, '0')}–{String(a.to).padStart(2, '0')}
                  </span>
                  <span>{a.label}</span>
                </li>
              ))}
            </ol>
          </section>
          <button
            type="submit"
            className="rounded-full bg-primary px-6 py-3 text-sm font-bold text-primary-foreground hover:bg-primary-hover"
          >
            Choose an advocate and time
          </button>
          <button type="button" onClick={() => navigate('/lawyers')} className="text-[13px] text-muted hover:text-ink">
            Skip planning
          </button>
        </aside>
      </form>
    </div>
  )
}
