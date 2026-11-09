import { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, CircleAlert, Database, FileText, KeyRound, Loader2, Play, Search } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { toast } from 'sonner'
import { getApiErrorMessage, getLibrary, searchLibrary, startIngestion } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import type { IngestionJob, LibraryOverview, LibrarySearch } from '../types'

const mono = 'font-mono text-[10.5px] uppercase tracking-[0.14em]'

// The LlamaIndex pipeline each act goes through; stage names match the job rows the backend writes.
const STAGES: { key: string; label: string; tech: string }[] = [
  { key: 'fetch', label: 'Fetch', tech: 'PDFReader' },
  { key: 'parse', label: 'Parse', tech: 'pages → one Document' },
  { key: 'split', label: 'Split', tech: 'SectionNodeParser' },
  { key: 'embed', label: 'Embed', tech: 'AzureOpenAIEmbedding · 1536-d' },
  { key: 'index', label: 'Index', tech: 'PGVectorStore + full text' },
  { key: 'eval', label: 'Check', tech: 'section table · golden set' },
]

const fmtTime = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'

function stageIndex(job: IngestionJob | null) {
  if (!job) return -1
  if (job.status === 'ok') return STAGES.length
  return STAGES.findIndex((s) => s.key === job.stage)
}

function Check({ ok, title, fix, icon: Icon }: { ok: boolean; title: string; fix: string; icon: typeof Database }) {
  return (
    <div className={`flex gap-3 rounded-2xl border p-4 ${ok ? 'border-success-text/30 bg-success-bg/40' : 'border-warn-text/30 bg-warn-text/5'}`}>
      <Icon className={`mt-0.5 size-5 flex-none ${ok ? 'text-success-text' : 'text-warn-text'}`} />
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-[14px] font-semibold">
          {title}
          {ok ? <CheckCircle2 className="size-4 text-success-text" /> : <CircleAlert className="size-4 text-warn-text" />}
        </div>
        <div className="mt-0.5 text-[12.5px] text-muted">{ok ? 'Ready' : fix}</div>
      </div>
    </div>
  )
}

export default function LibraryPage() {
  const reduce = useReducedMotion()
  const [lib, setLib] = useState<LibraryOverview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [picked, setPicked] = useState<string[]>([])
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [query, setQuery] = useState('punishment for theft')
  const [asOf, setAsOf] = useState('')
  const [searching, setSearching] = useState(false)
  const [result, setResult] = useState<LibrarySearch | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)

  const load = useCallback(() => {
    getLibrary()
      .then((data) => {
        setLib(data)
        setError(null)
      })
      .catch((err) => setError(getApiErrorMessage(err)))
  }, [])

  useEffect(load, [load])

  const running = !!lib?.jobs.some((j) => j.status === 'running')
  useEffect(() => {
    if (!running) return
    const t = window.setInterval(load, 3000)
    return () => window.clearInterval(t)
  }, [running, load])

  if (error && !lib) return <ErrorState message={error} onRetry={load} />
  if (!lib) return <LoadingState label="Opening the law library…" />

  const pdfs = lib.acts.filter((a) => a.pdf_present).length
  const ready = lib.reachable && lib.azure
  const ingested = lib.acts.filter((a) => a.sections > 0).length
  const toggle = (code: string) => setPicked((p) => (p.includes(code) ? p.filter((c) => c !== code) : [...p, code]))
  const current = lib.jobs.find((j) => j.status === 'running') ?? lib.jobs[0] ?? null
  const at = stageIndex(current)

  async function ingest() {
    setStarting(true)
    setStartError(null)
    try {
      const { started } = await startIngestion(picked)
      toast.success(`Ingestion started: ${started.join(', ')}`)
      setPicked([])
      window.setTimeout(load, 800)
    } catch (err) {
      setStartError(getApiErrorMessage(err))
    } finally {
      setStarting(false)
    }
  }

  async function search() {
    if (query.trim().length < 2) return
    setSearching(true)
    setSearchError(null)
    try {
      setResult(await searchLibrary(query.trim(), asOf))
    } catch (err) {
      setSearchError(getApiErrorMessage(err))
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-10">
      <div className="mx-auto flex max-w-[1080px] flex-col gap-8 pb-8">
        <div>
          <div className={`${mono} text-brass-light`}>§ Law library</div>
          <h1 className="mt-2 font-display text-[32px] font-semibold leading-tight tracking-[-0.01em] md:text-[40px]">
            Bare acts the agents read from
          </h1>
          <div className="mt-1 max-w-[70ch] text-sm text-muted">
            Official PDFs from India Code go through a LlamaIndex pipeline into pgvector. The chat agent retrieves
            from the same index, with vector and full-text search fused, filtered to the law in force on the incident
            date.
          </div>
        </div>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Check
            ok={lib.reachable}
            icon={Database}
            title="Vector database"
            fix="Postgres with pgvector is not answering. Run `docker compose up -d` in backend/."
          />
          <Check
            ok={lib.azure}
            icon={KeyRound}
            title="Embedding key"
            fix="Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in backend/.env, then restart the API."
          />
          <Check
            ok={pdfs === lib.acts.length}
            icon={FileText}
            title={`Act PDFs (${pdfs}/${lib.acts.length})`}
            fix="Put the PDFs in backend/data/raw/ (run `uv run nya-agent fetch`)."
          />
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="font-display text-[24px] font-semibold">Ingestion pipeline</h2>
            <span className="rounded-full border border-line px-2.5 py-1 font-mono text-[10.5px] tracking-[0.1em] text-muted">
              {current ? `LAST RUN · ${current.act} · ${current.status.toUpperCase()}` : 'NO RUNS YET'}
            </span>
          </div>
          <div className="overflow-x-auto rounded-2xl border border-line bg-well/50 p-4">
            <ol className="flex min-w-[760px] items-stretch gap-2">
              {STAGES.map((s, i) => {
                const done = at > i
                const live = current?.status === 'running' && at === i
                const failed = current?.status === 'failed' && at === i
                return (
                  <li key={s.key} className="flex flex-1 items-stretch gap-2">
                    <div
                      className={`relative flex-1 rounded-xl border px-3 py-2.5 transition-colors ${
                        failed
                          ? 'border-warn-text/50 bg-warn-text/10'
                          : live
                            ? 'border-brass bg-brass/10'
                            : done
                              ? 'border-success-text/40 bg-success-bg/40'
                              : 'border-line'
                      }`}
                    >
                      {live && !reduce && (
                        <motion.span
                          aria-hidden
                          className="absolute inset-0 rounded-xl ring-2 ring-brass/40"
                          animate={{ opacity: [0.2, 0.9, 0.2] }}
                          transition={{ duration: 1.6, repeat: Infinity }}
                        />
                      )}
                      <div className="font-mono text-[10px] text-faint">0{i + 1}</div>
                      <div className="text-[13.5px] font-semibold">{s.label}</div>
                      <div className="mt-0.5 font-mono text-[10.5px] leading-snug text-muted">{s.tech}</div>
                    </div>
                    {i < STAGES.length - 1 && <span className={`h-px w-3 flex-none self-center ${done ? 'bg-success-text' : 'bg-line'}`} />}
                  </li>
                )
              })}
            </ol>
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-[24px] font-semibold">Acts</h2>
              <div className="mt-0.5 text-[13px] text-muted">
                {ingested} of {lib.acts.length} in the library. Re-running an act replaces only that act.
              </div>
            </div>
            <button
              onClick={ingest}
              disabled={!ready || picked.length === 0 || starting || running}
              title={!ready ? 'Fix the checks above first' : picked.length === 0 ? 'Pick at least one act' : undefined}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-[13px] font-bold text-primary-foreground shadow-card transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-45"
            >
              {starting || running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              {running ? 'Ingesting…' : `Ingest ${picked.length ? picked.join(', ') : 'selected'}`}
            </button>
          </div>
          {startError && <div className="rounded-xl border border-warn-text/30 bg-warn-text/5 px-4 py-3 text-[13px] text-warn-text">{startError}</div>}
          <div className="overflow-x-auto rounded-2xl border border-line">
            <table className="w-full min-w-[720px] border-collapse text-[13.5px]">
              <thead>
                <tr className={`${mono} text-left text-faint`}>
                  <th className="w-10 px-4 py-3 font-medium" />
                  <th className="px-3 py-3 font-medium">Act</th>
                  <th className="px-3 py-3 font-medium">In force</th>
                  <th className="px-3 py-3 text-right font-medium">Sections</th>
                  <th className="px-3 py-3 font-medium">PDF</th>
                  <th className="px-3 py-3 font-medium">Last ingested</th>
                </tr>
              </thead>
              <tbody>
                {lib.acts.map((a) => (
                  <tr key={a.code} className="border-t border-line transition-colors hover:bg-fg/[0.03]">
                    <td className="px-4 py-3">
                      <input
                        id={`act-${a.code}`}
                        type="checkbox"
                        checked={picked.includes(a.code)}
                        onChange={() => toggle(a.code)}
                        aria-label={`Select ${a.title}`}
                        className="size-4 accent-[rgb(var(--ring))]"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <label htmlFor={`act-${a.code}`} className="cursor-pointer">
                        <span className="font-mono text-[12px] text-brass-light">{a.code}</span>{' '}
                        <span className="font-semibold">{a.title}</span>
                      </label>
                    </td>
                    <td className="px-3 py-3 font-mono text-[11.5px]">
                      {a.repealed_on ? (
                        <span className="text-warn-text">REPEALED {a.repealed_on} → {a.replaced_by}</span>
                      ) : (
                        <span className="text-success-text">FROM {a.in_force_from}</span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-right font-mono tabular-nums">{a.sections || '—'}</td>
                    <td className="px-3 py-3">
                      {a.pdf_present ? <CheckCircle2 className="size-4 text-success-text" /> : <span className="font-mono text-[11px] text-warn-text">MISSING</span>}
                    </td>
                    <td className="px-3 py-3 font-mono text-[11.5px] text-muted">
                      {a.last_job?.status === 'failed' ? <span className="text-warn-text">FAILED · {a.last_job.stage}</span> : fmtTime(a.ingested_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {lib.jobs.length > 0 && (
            <details className="rounded-2xl border border-line px-4 py-3">
              <summary className="cursor-pointer font-mono text-[11px] tracking-[0.1em] text-muted">RECENT RUNS ({lib.jobs.length})</summary>
              <ul className="mt-3 flex flex-col gap-1.5 font-mono text-[11.5px]">
                {lib.jobs.map((j) => (
                  <li key={j.id} className="flex flex-wrap gap-x-3 text-muted">
                    <span className="text-ink">{j.act}</span>
                    <span className={j.status === 'failed' ? 'text-warn-text' : j.status === 'ok' ? 'text-success-text' : 'text-brass-light'}>
                      {j.status.toUpperCase()}
                    </span>
                    <span>{j.stage}</span>
                    <span>{fmtTime(j.started_at)}</span>
                    {Object.entries(j.stats).map(([k, v]) => (
                      <span key={k}>
                        {k}={String(v)}
                      </span>
                    ))}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <div>
            <h2 className="font-display text-[24px] font-semibold">Test retrieval</h2>
            <div className="mt-0.5 max-w-[70ch] text-[13px] text-muted">
              Ask the library directly. These are the sections the chat agent would read for the same question and
              date: LlamaIndex vector search and full-text search, fused by reciprocal rank.
            </div>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              search()
            }}
            className="flex flex-col gap-2 sm:flex-row"
          >
            <label htmlFor="lib-q" className="sr-only">
              Question
            </label>
            <input
              id="lib-q"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. punishment for theft, BNS 303, cheating"
              className="min-w-0 flex-1 rounded-xl border border-line bg-surface px-4 py-3 text-[14.5px]"
            />
            <label className="flex items-center gap-2 rounded-xl border border-line bg-surface px-3 font-mono text-[11px] tracking-[0.08em] text-muted">
              LAW ON
              <input
                id="lib-asof"
                type="date"
                value={asOf}
                onChange={(e) => setAsOf(e.target.value)}
                className="bg-transparent py-2.5 text-[12.5px] text-ink [color-scheme:dark]"
              />
            </label>
            <button
              type="submit"
              disabled={searching}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-[13px] font-bold text-primary-foreground transition-colors hover:bg-primary-hover disabled:opacity-60"
            >
              {searching ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
              Retrieve
            </button>
          </form>
          {searchError && <div className="text-[13px] text-warn-text">{searchError}</div>}
          {result && (
            <div className="flex flex-col gap-2.5">
              <div className="flex flex-wrap gap-2 font-mono text-[10.5px] tracking-[0.08em]">
                <span className="rounded-full border border-line px-2.5 py-1 text-muted">
                  MODE · {result.mode === 'hybrid' ? 'HYBRID (VECTOR + BM25)' : 'EXACT SECTION NUMBERS ONLY'}
                </span>
                <span className="rounded-full border border-line px-2.5 py-1 text-muted">LAW ON {result.as_of}</span>
                <span className="rounded-full border border-line px-2.5 py-1 text-muted">IN SCOPE · {result.acts_in_scope.join(' · ')}</span>
              </div>
              {!result.library_ok && (
                <div className="rounded-xl border border-warn-text/30 bg-warn-text/5 px-4 py-3 text-[13px] text-warn-text">
                  The library did not answer, so nothing was retrieved. Check the vector database above.
                </div>
              )}
              {result.library_ok && result.hits.length === 0 && (
                <div className="rounded-xl border border-dashed border-line px-4 py-3 text-[13px] text-muted">
                  {result.mode === 'exact'
                    ? 'No section matched. Without the embedding key only section numbers work, e.g. "BNS 303".'
                    : 'No sections matched this question.'}
                </div>
              )}
              <ol className="fx-stagger flex flex-col gap-2.5">
                {result.hits.map((h, i) => (
                  <li key={`${h.act}-${h.section}`} className="rounded-2xl border border-line bg-surface p-4">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span className="font-mono text-[11px] text-faint">#{i + 1}</span>
                      <span className="font-mono text-[12.5px] text-brass-light">
                        {h.act} s.{h.section}
                      </span>
                      <span className="font-semibold">{h.heading}</span>
                      <span className="ml-auto font-mono text-[10.5px] text-muted">
                        {h.found_by.toUpperCase()} · SCORE {h.score.toFixed(3)}
                        {h.page ? ` · P.${h.page}` : ''}
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-3 text-[13.5px] leading-relaxed text-body2">{h.text}</p>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
