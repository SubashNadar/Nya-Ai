import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import type { Matter, MatterStatus } from '../types'

// The BNS, BNSS and BSA replaced the IPC, CrPC and Evidence Act on this date.
const CUTOVER = new Date('2024-07-01T00:00:00')
const DAY = 86_400_000

export const STATUS: Record<MatterStatus, { label: string; cls: string; dot: string }> = {
  answered: { label: 'ANSWERED', cls: 'border-brass/40 bg-brass/10 text-brass-light', dot: '#D9B56E' },
  reviewed: { label: 'ADVOCATE CHECKED', cls: 'border-success-text/40 bg-success-bg text-success-text', dot: '#5CC79A' },
  advocate_review: { label: 'ADVOCATE REVIEW', cls: 'border-sky-300/40 bg-sky-300/10 text-sky-300', dot: '#7DD3FC' },
  lawyer_suggested: { label: 'LAWYER SUGGESTED', cls: 'border-success-text/40 bg-success-bg text-success-text', dot: '#5CC79A' },
  emergency: { label: 'EMERGENCY · 112', cls: 'border-warn-text/40 bg-warn-text/10 text-warn-text', dot: '#E2876B' },
  refused: { label: 'NOT ANSWERED', cls: 'border-white/15 bg-white/5 text-white/60', dot: '#8C9AB3' },
}

const W = 1000
const H = 300
const AXIS = 158
const PAD = 40

const fmt = (iso: string) =>
  new Date(iso + 'T00:00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

const LABEL = 28
const short = (s: string, n = LABEL) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s)

export function MattersTimeline({ matters }: { matters: Matter[] }) {
  const navigate = useNavigate()
  const reduce = useReducedMotion()
  const dated = useMemo(
    () =>
      matters
        .filter((m) => m.incident_date)
        .sort((a, b) => (a.incident_date! < b.incident_date! ? -1 : 1)),
    [matters],
  )
  const undated = matters.filter((m) => !m.incident_date)
  const [picked, setPicked] = useState<string | null>(() => (dated.at(-1) ?? matters[0])?.question_id ?? null)
  const sel = matters.find((m) => m.question_id === picked) ?? null

  const { x, start, end, nodes } = useMemo(() => {
    const today = new Date()
    const first = dated[0] ? new Date(dated[0].incident_date! + 'T00:00:00') : today
    const start = new Date(Math.min(new Date('2024-01-01T00:00:00').getTime(), first.getTime() - 30 * DAY))
    const end = new Date(today.getTime() + 45 * DAY)
    const x = (d: Date) => PAD + ((d.getTime() - start.getTime()) / (end.getTime() - start.getTime())) * (W - 2 * PAD)
    // Greedy lanes so labels never sit on top of each other: above and below the axis, nearest first.
    // A label runs right of its pin, or left of it near the right edge.
    const lanes = [-1, 1, -2, 2, -3, 3]
    const taken: Record<number, [number, number][]> = {}
    const nodes = dated.map((m, i) => {
      const nx = x(new Date(m.incident_date! + 'T00:00:00'))
      const width = Math.min(m.question.length, LABEL) * 6.9 + 22
      const right = nx > W - 230
      const span: [number, number] = right ? [nx - width, nx + 10] : [nx - 10, nx + width]
      const free = (l: number) => !(taken[l] ?? []).some(([a, b]) => span[0] < b && a < span[1])
      const lane = lanes.find(free) ?? lanes[i % lanes.length]
      taken[lane] = [...(taken[lane] ?? []), span]
      return { m, nx, ny: AXIS + lane * 38, right }
    })
    return { x, start, end, nodes }
  }, [dated])

  const cut = x(CUTOVER)
  const years: number[] = []
  for (let y = start.getFullYear() + (start.getMonth() > 0 ? 1 : 0); y <= end.getFullYear(); y++) years.push(y)

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-2xl border border-line bg-navy-950/50">
        <svg viewBox={`0 0 ${W} ${H}`} className="block w-full min-w-[720px]" role="img" aria-label="Your questions placed by the date of the incident">
          <rect x={PAD} y={18} width={Math.max(0, cut - PAD)} height={H - 36} fill="rgba(226,135,107,0.07)" />
          <rect x={cut} y={18} width={W - PAD - cut} height={H - 36} fill="rgba(92,199,154,0.045)" />
          <text x={PAD + 8} y={38} className="fill-warn-text font-mono text-[10.5px] tracking-[0.12em]">
            IPC · CrPC
          </text>
          <text x={cut + 8} y={38} className="fill-success-text font-mono text-[10.5px] tracking-[0.12em]">
            BNS · BNSS · BSA IN FORCE
          </text>
          <line x1={cut} y1={18} x2={cut} y2={H - 18} stroke="#D9B56E" strokeWidth={1.5} strokeDasharray="4 4" />
          <text x={cut - 6} y={H - 26} textAnchor="end" className="fill-brass-light font-mono text-[10.5px]">
            1 JUL 2024
          </text>
          <line x1={PAD} y1={AXIS} x2={W - PAD} y2={AXIS} stroke="rgba(214,226,255,0.25)" />
          {years.map((y) => {
            const yx = x(new Date(`${y}-01-01T00:00:00`))
            return (
              <g key={y}>
                <line x1={yx} y1={AXIS - 5} x2={yx} y2={AXIS + 5} stroke="rgba(214,226,255,0.35)" />
                <text x={yx + 4} y={AXIS + 18} className="fill-muted font-mono text-[10.5px]">
                  {y}
                </text>
              </g>
            )
          })}
          {(() => {
            const tx = x(new Date())
            return (
              <g>
                <line x1={tx} y1={18} x2={tx} y2={H - 18} stroke="rgba(238,242,248,0.25)" strokeDasharray="2 4" />
                <text x={tx - 6} y={H - 26} textAnchor="end" className="fill-white/70 font-mono text-[10px]">
                  TODAY
                </text>
              </g>
            )
          })()}
          {nodes.map(({ m, nx, ny, right }, i) => {
            const on = m.question_id === picked
            const dot = STATUS[m.status].dot
            return (
              <motion.g
                key={m.question_id}
                role="button"
                tabIndex={0}
                aria-label={`${m.question}, incident ${fmt(m.incident_date!)}`}
                aria-pressed={on}
                onClick={() => setPicked(m.question_id)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setPicked(m.question_id)}
                onMouseEnter={() => setPicked(m.question_id)}
                className="cursor-pointer outline-none"
                initial={reduce ? false : { opacity: 0, y: ny < AXIS ? 10 : -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.06 * i, duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
              >
                <line x1={nx} y1={AXIS} x2={nx} y2={ny} stroke={dot} strokeOpacity={on ? 0.9 : 0.45} />
                <circle cx={nx} cy={AXIS} r={3} fill={dot} />
                <circle cx={nx} cy={ny} r={on ? 8 : 6} fill={dot} stroke="#0E1A2E" strokeWidth={2} />
                {on && <circle cx={nx} cy={ny} r={14} fill="none" stroke={dot} strokeOpacity={0.5} />}
                <text
                  x={right ? nx - 14 : nx + 14}
                  y={ny + 4}
                  textAnchor={right ? 'end' : 'start'}
                  className={`text-[12.5px] ${on ? 'fill-white font-semibold' : 'fill-white/75'}`}
                >
                  {short(m.question)}
                </text>
              </motion.g>
            )
          })}
          {dated.length === 0 && (
            <text x={W / 2} y={AXIS - 28} textAnchor="middle" className="fill-muted text-[13px]">
              Add “When did it happen?” in chat to place a question on this line.
            </text>
          )}
        </svg>
      </div>

      {undated.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[10.5px] tracking-[0.12em] text-faint">NO INCIDENT DATE</span>
          {undated.slice(0, 8).map((m) => (
            <button
              key={m.question_id}
              onClick={() => setPicked(m.question_id)}
              aria-pressed={m.question_id === picked}
              className={`rounded-full border px-3 py-1 text-[12.5px] transition-colors ${
                m.question_id === picked ? 'border-brass/60 bg-brass/10 text-white' : 'border-line text-body2 hover:text-ink'
              }`}
            >
              {short(m.question, 38)}
            </button>
          ))}
        </div>
      )}

      {sel && (
        <motion.div
          key={sel.question_id}
          initial={reduce ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 sm:flex-row sm:items-center"
          aria-live="polite"
        >
          <div className="min-w-0 flex-1">
            <div className="font-display text-[18px] leading-snug">{sel.question}</div>
            <div className="mt-1 font-mono text-[11.5px] text-muted">
              {sel.citation ? `${sel.citation} · ` : ''}
              {sel.incident_date
                ? `Incident ${fmt(sel.incident_date)}: ${sel.code === 'old' ? 'before 1 Jul 2024, so the IPC and CrPC apply' : 'the BNS, BNSS and BSA apply'}`
                : 'No incident date: answered on the law in force today'}
            </div>
          </div>
          <span className={`w-fit whitespace-nowrap rounded-full border px-2.5 py-1 font-mono text-[10.5px] tracking-[0.08em] ${STATUS[sel.status].cls}`}>
            {STATUS[sel.status].label}
          </span>
          <button
            onClick={() => navigate(`/chat?c=${sel.conversation_id}`)}
            className="inline-flex w-fit items-center gap-1.5 rounded-full border border-line px-4 py-2 text-[13px] font-semibold text-ink transition-colors hover:border-brass/60"
          >
            Open conversation
            <ArrowUpRight className="size-3.5" />
          </button>
        </motion.div>
      )}
    </div>
  )
}
