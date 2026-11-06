import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowUp, Briefcase, Check, Copy, FileText, Home, type LucideIcon, Scale, ShieldAlert } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { LogoMark } from '../components/Logo'
import { getApiErrorMessage, sendChatMessage } from '../lib/api'
import type { ChatMessage } from '../types'

const QUICK_REPLIES: { text: string; topic: string; icon: LucideIcon }[] = [
  { text: 'What is theft under Indian law?', topic: 'Criminal', icon: ShieldAlert },
  { text: 'My landlord won’t return my deposit', topic: 'Property', icon: Home },
  { text: 'How do I file an FIR?', topic: 'Police', icon: FileText },
  { text: 'Employer is holding my final salary', topic: 'Employment', icon: Briefcase },
]

// The BNS replaced the IPC for offences on or after this date.
const BNS_FROM = '2024-07-01'

// Well-known IPC to BNS correspondences. The full table comes from the official comparison
// table when the law library is ingested; until then these are shown as examples only.
const CONCORDANCE: { ipc: string; bns: string; label: string }[] = [
  { ipc: 's.302', bns: 's.103', label: 'Murder' },
  { ipc: 's.378–379', bns: 's.303', label: 'Theft' },
  { ipc: 's.420', bns: 's.318', label: 'Cheating' },
  { ipc: 's.425–427', bns: 's.324', label: 'Mischief' },
]

const GREETING: ChatMessage = {
  id: 'greeting',
  role: 'ai',
  text: "Namaste! I'm Nya-AI, your free AI legal assistant. Ask me anything — theft, rent disputes, FIRs, divorce, salary issues — and I'll explain your rights in plain language, grounded in Indian law.",
  points: [],
  citation: '',
  cta: false,
  created_at: new Date().toISOString(),
}

interface TraceStep {
  name: string
  detail: string
  done: boolean
}

interface Turn {
  question: string
  askedAt: string
  ms: number
  steps: TraceStep[]
}

const enter = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.25, ease: 'easeOut' },
} as const

const mono = 'font-mono text-[10.5px] uppercase tracking-[0.14em]'

// "Sources: IPC §378, §379" -> ["IPC §378", "IPC §379"]: a bare section inherits the act named before it.
function sources(citation: string): string[] {
  let act = ''
  return citation
    .replace(/^Sources?:\s*/i, '')
    .split(/[;,]\s*/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => {
      const named = s.match(/^(.+?)\s+§/)
      if (named) act = named[1]
      else if (s.startsWith('§') && act) return `${act} ${s}`
      return s
    })
}

function timeIST(iso: string) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Kolkata' })
}

function CopyAnswer({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    const body = [message.text, ...message.points.map((p) => `• ${p}`), message.citation].filter(Boolean).join('\n')
    try {
      await navigator.clipboard.writeText(body)
      setCopied(true)
      toast.success('Answer copied')
      setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error('Could not copy')
    }
  }
  return (
    <button
      type="button"
      onClick={copy}
      className="inline-flex h-9 items-center gap-2 rounded-lg border border-line px-3 text-[13px] font-semibold text-ink transition-colors hover:border-focus"
    >
      {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
      {copied ? 'Copied' : 'Copy with sources'}
    </button>
  )
}

function TypingIndicator() {
  return (
    <motion.div {...enter} exit={{ opacity: 0 }} className="flex items-center gap-3 self-start">
      <span className={`${mono} text-brass-light`}>Working</span>
      <span className="h-[6px] w-[6px] animate-dotpulse rounded-full bg-primary [animation-delay:0s]" />
      <span className="h-[6px] w-[6px] animate-dotpulse rounded-full bg-primary [animation-delay:0.15s]" />
      <span className="h-[6px] w-[6px] animate-dotpulse rounded-full bg-primary [animation-delay:0.3s]" />
    </motion.div>
  )
}

function Answer({ m, index, onLawyer }: { m: ChatMessage; index: number; onLawyer: () => void }) {
  const refs = sources(m.citation)
  const paragraphs = [m.text, ...m.points]
  return (
    <motion.article
      {...enter}
      className="overflow-hidden rounded-2xl border border-brass-light/35 bg-surface/95 shadow-card"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3 md:px-6">
        <span className={`${mono} text-brass-light`}>Legal information · not legal advice</span>
        <span className={`${mono} text-faint`}>Ref NYA/ANS/{String(index).padStart(2, '0')}</span>
      </div>
      <div className="flex flex-col gap-3 px-5 py-5 md:px-6">
        {paragraphs.map((p, i) => (
          <div key={i} className="grid grid-cols-[34px_1fr] gap-2 text-[15px] leading-[1.65] text-body3">
            <span className="pt-0.5 font-mono text-xs text-brass-light">¶{i + 1}</span>
            <span>
              {p}
              {i === 0 && refs.length > 0 && <sup className="ml-0.5 font-mono text-[11px] text-brass-light">[1]</sup>}
            </span>
          </div>
        ))}
      </div>
      {refs.length > 0 && (
        <div className="flex flex-col border-t border-line">
          {refs.map((r, i) => (
            <div
              key={r}
              className="grid grid-cols-[34px_1fr] gap-2 border-b border-line/60 px-5 py-2.5 font-mono text-[12.5px] last:border-b-0 md:px-6"
            >
              <span className="text-brass-light">[{i + 1}]</span>
              <span className="text-ink">{r}</span>
            </div>
          ))}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2 border-t border-line px-5 py-3 md:px-6">
        <CopyAnswer message={m} />
        <div className="flex-1" />
        <Button onClick={onLawyer} className="h-9 rounded-lg px-4 text-[13px]">
          <Scale className="size-4" />
          Ask an advocate
        </Button>
      </div>
    </motion.article>
  )
}

function TracePanel({ turn }: { turn: Turn | null }) {
  return (
    <aside aria-label="Reasoning trace" className="hidden w-[260px] flex-none flex-col gap-4 overflow-y-auto border-r border-line p-5 lg:flex">
      <div className="flex items-center justify-between">
        <span className={`${mono} text-brass-light`}>Reasoning trace</span>
        {turn && <span className="font-mono text-[11px] text-faint">{(turn.ms / 1000).toFixed(2)}s</span>}
      </div>
      {turn ? (
        <ol className="flex flex-col gap-3">
          {turn.steps.map((s) => (
            <li key={s.name} className="grid grid-cols-[18px_1fr] gap-2">
              <span className={`font-mono text-xs ${s.done ? 'text-success-text' : 'text-faint'}`}>{s.done ? '✓' : '○'}</span>
              <div>
                <div className="font-mono text-[12.5px] text-ink">{s.name}</div>
                <div className="mt-0.5 text-[12px] leading-snug text-muted">{s.detail}</div>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-[13px] leading-relaxed text-muted">Each step Nya-AI takes to answer will appear here.</p>
      )}
      <div className="mt-auto rounded-xl border border-warn-border bg-warn-bg p-3 text-[12px] leading-relaxed text-warn-text">
        Basic mode: answers come from a keyword engine and may cite the old IPC. The Nya-AI agent, with BNS citations
        and checks, is being built.
      </div>
    </aside>
  )
}

function LawPanel() {
  const [incident, setIncident] = useState(() => new Date().toISOString().slice(0, 10))
  const bns = incident >= BNS_FROM
  const fmt = (d: string) => d.split('-').reverse().join('.')
  return (
    <aside aria-label="Applicable law" className="hidden w-[300px] flex-none flex-col gap-4 overflow-y-auto border-l border-line p-5 xl:flex">
      <section className="rounded-2xl border border-line bg-surface/90 p-4">
        <div className={`${mono} text-brass-light`}>Temporal jurisdiction</div>
        <ol className="relative mt-4 flex flex-col gap-4 border-l border-line pl-4">
          <li className="relative">
            <span className="absolute -left-[21px] top-1.5 size-2.5 rounded-full border border-faint bg-bg" />
            <div className="flex items-center justify-between gap-2 text-[13px] font-semibold">
              Indian Penal Code, 1860
              <span className="font-mono text-[10px] text-faint">REPEALED</span>
            </div>
            <div className="mt-0.5 font-mono text-[11.5px] text-muted">06.10.1860 → 30.06.2024</div>
          </li>
          <li className="relative">
            <span className="absolute -left-[21px] top-1.5 size-2.5 rounded-full bg-success-dark" />
            <div className="flex items-center justify-between gap-2 text-[13px] font-semibold">
              Bharatiya Nyaya Sanhita
              <span className="font-mono text-[10px] text-success-text">IN FORCE</span>
            </div>
            <div className="mt-0.5 font-mono text-[11.5px] text-muted">01.07.2024 → present</div>
          </li>
          <li className="relative">
            <span className="absolute -left-[22px] top-1 size-3 rotate-45 bg-primary" />
            <div className="font-mono text-[11.5px] text-brass-light">INCIDENT · {fmt(incident)}</div>
            <div className="mt-0.5 text-[13px] font-semibold">{bns ? 'BNS governs this matter' : 'IPC governs this matter'}</div>
          </li>
        </ol>
        <label htmlFor="incident-date" className="mt-4 block text-[12px] font-semibold text-muted">
          Change incident date
        </label>
        <input
          id="incident-date"
          type="date"
          value={incident}
          onChange={(e) => e.target.value && setIncident(e.target.value)}
          className="mt-1.5 h-10 w-full rounded-lg border border-input bg-bg px-3 font-mono text-[13px] text-ink [color-scheme:dark]"
        />
      </section>
      <section className="rounded-2xl border border-line bg-surface/90 p-4">
        <div className={`${mono} text-brass-light`}>Section concordance</div>
        <div className="mt-3 grid grid-cols-[1fr_20px_1fr] gap-y-2 font-mono text-[12.5px]">
          <span className="text-faint">IPC</span>
          <span />
          <span className="text-faint">BNS</span>
          {CONCORDANCE.map((c) => (
            <div key={c.ipc} className="contents" title={c.label}>
              <span>{c.ipc}</span>
              <span className="text-brass-light">→</span>
              <span className="text-success-text">{c.bns}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
          Examples from the official IPC to BNS comparison table. Check the full section text before relying on it.
        </p>
      </section>
    </aside>
  )
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | undefined>(undefined)
  const scrollRef = useRef<HTMLDivElement>(null)
  const started = messages.length > 1

  useEffect(() => {
    if (!started) return
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, typing, started])

  async function send(text: string) {
    const msg = text.trim()
    if (!msg || typing) return
    setError(null)
    const askedAt = new Date().toISOString()
    setMessages((prev) => [
      ...prev,
      { id: `local-${Date.now()}`, role: 'user', text: msg, points: [], citation: '', cta: false, created_at: askedAt },
    ])
    setInput('')
    setTyping(true)
    const t0 = performance.now()
    try {
      const res = await sendChatMessage(msg, conversationId)
      const ms = performance.now() - t0
      setConversationId(res.conversation_id)
      setMessages((prev) => [
        ...prev,
        {
          id: res.id,
          role: 'ai',
          text: res.text,
          points: res.points,
          citation: res.citation,
          cta: res.cta,
          created_at: new Date().toISOString(),
        },
      ])
      const refs = sources(res.citation)
      setTurns((prev) => [
        ...prev,
        {
          question: msg,
          askedAt,
          ms,
          steps: [
            { name: 'request', detail: 'question sent to the Nya-AI API', done: true },
            { name: 'engine', detail: 'keyword rule engine (basic mode)', done: true },
            {
              name: 'citations',
              detail: refs.length ? `${refs.length} source${refs.length > 1 ? 's' : ''} named` : 'no source named',
              done: refs.length > 0,
            },
            { name: 'advocate_review', detail: res.cta ? 'advocate suggested' : 'not needed', done: res.cta },
          ],
        },
      ])
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setTyping(false)
    }
  }

  const lastTurn = turns.at(-1) ?? null
  const matter = useMemo(() => (conversationId ? conversationId.slice(0, 8).toUpperCase() : 'NEW'), [conversationId])
  let answerCount = 0

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-none flex-wrap items-center gap-x-5 gap-y-1 border-b border-line bg-bg/80 px-5 py-3 font-mono text-[11px] tracking-[0.08em] text-muted backdrop-blur md:px-8">
        <span>
          MATTER <span className="text-ink">{matter}</span>
        </span>
        <span className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-warn-text" />
          ENGINE · BASIC MODE
        </span>
        <span className="hidden sm:inline">
          JURISDICTION <span className="text-ink">IN</span>
        </span>
      </div>

      <div className="flex min-h-0 flex-1">
        <TracePanel turn={lastTurn} />

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div ref={scrollRef} className="flex-1 overflow-y-auto">
            <div className="mx-auto flex w-full max-w-[780px] flex-col gap-5 px-4 py-6 md:px-8 md:py-8">
              {!started ? (
                <motion.div {...enter} className="flex flex-col items-center pt-2 text-center md:pt-10">
                  <LogoMark size={64} tone="brass" />
                  <div className={`${mono} mt-5 text-brass-light`}>Indian law, cited</div>
                  <h1 className="mt-3 font-display text-[30px] font-semibold leading-tight text-brass-soft md:text-[38px]">
                    Namaste! I'm Nya-AI.
                  </h1>
                  <p className="mt-3 max-w-[560px] text-[15px] leading-[1.65] text-body2">
                    {GREETING.text.replace(/^Namaste! I'm Nya-AI, your/, 'Your')}
                  </p>
                  <div className="mt-8 grid w-full grid-cols-1 gap-3 text-left sm:grid-cols-2">
                    {QUICK_REPLIES.map((q, i) => (
                      <motion.button
                        key={q.text}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.06 * i, duration: 0.25 }}
                        onClick={() => send(q.text)}
                        className="group flex items-start gap-3 rounded-2xl border border-line bg-surface/90 p-4 text-left transition-colors hover:border-focus"
                      >
                        <div className="flex size-9 flex-none items-center justify-center rounded-xl bg-soft text-brass-light">
                          <q.icon className="size-[18px]" />
                        </div>
                        <div className="min-w-0">
                          <div className={`${mono} text-brass-light`}>{q.topic}</div>
                          <div className="mt-1 text-sm font-semibold text-ink">{q.text}</div>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                </motion.div>
              ) : (
                messages.map((m, i) => {
                  if (m.id === 'greeting') return null
                  if (m.role === 'user') {
                    return (
                      <motion.div key={m.id} {...enter} className="rounded-2xl border border-line bg-surface/70 px-5 py-4">
                        <div className={`${mono} text-faint`}>Query · {timeIST(m.created_at)} IST</div>
                        <div className="mt-1.5 text-[15.5px] leading-[1.55] text-ink">{m.text}</div>
                      </motion.div>
                    )
                  }
                  answerCount += 1
                  return (
                    <Answer
                      key={m.id}
                      m={m}
                      index={answerCount}
                      onLawyer={() =>
                        navigate('/plan', { state: { question: messages[i - 1]?.role === 'user' ? messages[i - 1].text : '' } })
                      }
                    />
                  )
                })
              )}
              <AnimatePresence>{typing && <TypingIndicator />}</AnimatePresence>
              {error && (
                <div className="self-start rounded-xl border border-warn-border bg-warn-bg px-4 py-3 text-[13px] font-medium text-warn-text">
                  {error}
                </div>
              )}
            </div>
          </div>

          <div className="flex-none px-4 pb-4 pt-2 md:px-8 md:pb-5">
            <div className="mx-auto w-full max-w-[780px]">
              <div className="flex items-center gap-2 rounded-2xl border border-brass-light/45 bg-surface p-2 pl-4 shadow-composer focus-within:border-focus">
                <span aria-hidden className="font-mono text-lg text-brass-light">
                  ›
                </span>
                <label htmlFor="chat-ask" className="sr-only">
                  Ask a legal question
                </label>
                <input
                  id="chat-ask"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && send(input)}
                  placeholder={started ? 'Ask a follow-up' : 'Ask any legal question: theft, rent, FIR, salary…'}
                  className="min-w-0 flex-1 bg-transparent py-2.5 text-[15px] text-ink placeholder:text-faint focus:outline-none"
                />
                <Button
                  onClick={() => send(input)}
                  disabled={typing || !input.trim()}
                  size="icon-lg"
                  aria-label="Send"
                  className="flex-none rounded-xl disabled:opacity-40"
                >
                  <ArrowUp className="size-5" />
                </Button>
              </div>
              <div className="mt-2 flex items-center justify-center gap-1.5 text-center text-[11.5px] text-muted">
                <ShieldAlert className="size-3.5 flex-none text-warn-text" />
                Legal information, not legal advice. For your own case, talk to an advocate. Emergency: call 112.
              </div>
            </div>
          </div>
        </div>

        <LawPanel />
      </div>
    </div>
  )
}
