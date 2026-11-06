import { useEffect, useState } from 'react'
import { BadgeCheck, Clock3, Languages, Star } from 'lucide-react'
import { motion } from 'motion/react'
import { useNavigate } from 'react-router-dom'
import { getApiErrorMessage, getLawyers } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import type { LawyerCard } from '../types'

const FILTERS = ['All', 'Criminal', 'Property', 'Family', 'Employment']

export default function LawyersPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('All')
  const [lawyers, setLawyers] = useState<LawyerCard[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    setError(null)
    getLawyers(filter)
      .then((res) => setLawyers(res.lawyers))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [filter])

  return (
    <div className="flex-1 overflow-y-auto px-5 py-8 md:px-10">
      <div className="text-[11px] font-bold uppercase tracking-[0.16em] text-brass-dark">Find a lawyer</div>
      <h1 className="mt-2 font-display text-[30px] font-semibold tracking-[-0.01em] md:text-[38px]">
        Verified lawyers, honest prices
      </h1>
      <div className="mt-2 text-sm text-muted">
        First consultation ₹500 · Your lawyer keeps 70% · Bar Council verified
      </div>

      <div className="mt-6 inline-flex flex-wrap gap-1 rounded-full border border-line bg-surface p-1 shadow-card">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-4 py-2 text-[13px] font-semibold transition-colors ${
              filter === f ? 'bg-primary text-primary-foreground shadow-sm' : 'text-body2 hover:bg-bg hover:text-ink'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading && <LoadingState label="Finding lawyers…" />}
      {!loading && error && <ErrorState message={error} onRetry={load} />}
      {!loading && !error && lawyers && lawyers.length === 0 && (
        <div className="mt-6 rounded-2xl border border-line bg-surface p-6 text-sm text-muted">
          No lawyers found in this category.
        </div>
      )}
      {!loading && !error && lawyers && lawyers.length > 0 && (
        <div className="mt-6 grid grid-cols-1 gap-5 [grid-template-columns:repeat(auto-fill,minmax(300px,1fr))] md:[grid-template-columns:repeat(auto-fill,minmax(340px,1fr))]">
          {lawyers.map((lw, i) => (
            <motion.div
              key={lw.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i, duration: 0.25, ease: 'easeOut' }}
              whileHover={{ y: -3 }}
              className="group flex flex-col overflow-hidden rounded-3xl border border-line bg-surface shadow-card transition-shadow hover:shadow-lift"
            >
              <div
                className="relative h-20"
                style={{
                  background: `linear-gradient(135deg, ${lw.avatar_color} 0%, ${lw.avatar_color}cc 55%, #0F1E33 100%)`,
                }}
              >
                <div
                  aria-hidden
                  className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.18)_1px,transparent_0)] [background-size:16px_16px]"
                />
                <div className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] font-bold text-white backdrop-blur">
                  <Star className="size-3.5 fill-brass-light text-brass-light" />
                  {lw.rating}
                  <span className="font-medium text-white/70">({lw.reviews})</span>
                </div>
              </div>
              <div className="flex flex-1 flex-col gap-4 px-5 pb-5">
              <div className="relative z-10 -mt-8 flex items-end gap-3.5">
                <div
                  className="flex h-[64px] w-[64px] flex-none items-center justify-center rounded-2xl text-[20px] font-bold text-white shadow-lift ring-4 ring-surface"
                  style={{ background: lw.avatar_color }}
                >
                  {lw.initials}
                </div>
              </div>
              <div className="flex items-center gap-3.5">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <div className="font-heading text-[17px] font-bold">{lw.name}</div>
                    <div className="inline-flex items-center gap-1 rounded-full bg-success-bg px-2.5 py-0.5 text-[11px] font-bold text-success-text">
                      <BadgeCheck className="size-3.5" />
                      Verified
                    </div>
                  </div>
                  <div className="mt-0.5 text-[13px] text-muted">
                    {lw.spec} · {lw.exp} yrs
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-body2">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-bg px-2.5 py-1.5">
                  <Languages className="size-3.5 text-muted" />
                  {lw.langs.join(' · ')}
                </div>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-bg px-2.5 py-1.5">
                  <Clock3 className="size-3.5 text-muted" />
                  Next: {lw.next_slot}
                </div>
              </div>
              <div className="mt-auto flex items-center gap-3 border-t border-line pt-4">
                <div className="flex-1">
                  <div className="font-heading text-xl font-extrabold text-ink">
                    ₹500{' '}
                    <span className="text-xs font-medium text-faint line-through">₹5,000</span>
                  </div>
                  <div className="text-[11px] text-muted">first video consult · 30 min</div>
                </div>
                <button
                  onClick={() => navigate(`/booking/${lw.id}`)}
                  className="rounded-full bg-primary hover:bg-primary-hover px-6 py-2.5 text-sm font-bold text-primary-foreground shadow-card transition-all hover:shadow-lift"
                >
                  Book
                </button>
              </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
