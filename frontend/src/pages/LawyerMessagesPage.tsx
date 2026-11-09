import { useEffect, useRef, useState } from 'react'
import { getApiErrorMessage, getMessageThreads, markThreadRead, replyToThread } from '../lib/api'
import { ErrorState, LoadingState } from '../components/states'
import type { MessageThread } from '../types'

export default function LawyerMessagesPage() {
  const [threads, setThreads] = useState<MessageThread[] | null>(null)
  const [selId, setSelId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  function load() {
    setLoading(true)
    setError(null)
    getMessageThreads()
      .then(({ threads: t }) => {
        setThreads(t)
        setSelId((prev) => prev ?? t[0]?.id ?? null)
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const selected = threads?.find((t) => t.id === selId) ?? null

  // Opening a thread explicitly marks it read server-side via PATCH .../read (the only way to
  // clear `unread` — there is no implicit clear-on-view/reply side effect anymore, see
  // docs/DECISIONS.md). The thread list already carries each thread's messages,
  // so no separate full-thread fetch is needed — just merge the updated thread back in.
  useEffect(() => {
    if (!selId) return
    markThreadRead(selId)
      .then((updated) => {
        setThreads((prev) => prev?.map((t) => (t.id === selId ? updated : t)) ?? null)
      })
      .catch((err) => setError(getApiErrorMessage(err)))
  }, [selId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [selected?.messages.length])

  async function sendReply() {
    const text = reply.trim()
    if (!text || !selected || sending) return
    setSending(true)
    try {
      const { message } = await replyToThread(selected.id, text)
      setThreads(
        (prev) =>
          prev?.map((t) =>
            t.id === selected.id ? { ...t, messages: [...t.messages, message] } : t,
          ) ?? null,
      )
      setReply('')
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  if (loading) return <LoadingState label="Loading messages…" />
  if (error && !threads) return <ErrorState message={error} onRetry={load} />
  if (!threads || threads.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-10 text-sm text-muted">
        No client messages yet.
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1">
      <div className="hidden w-[300px] flex-none overflow-y-auto border-r border-line bg-surface p-2.5 sm:block">
        <div className="px-2 pb-3 font-heading text-xl font-extrabold">Client messages</div>
        {threads.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelId(t.id)}
            className={`mb-1 flex w-full items-center gap-2.5 rounded-2xl p-3 text-left ${
              selId === t.id ? 'bg-soft' : 'bg-transparent'
            }`}
          >
            <div className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-full bg-soft text-[13px] font-bold text-primary">
              {t.client_initials}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-bold text-ink">{t.client_name}</div>
              <div className="mt-0.5 truncate text-[11px] text-muted">{t.topic}</div>
            </div>
            {t.unread && <div className="h-2 w-2 flex-none rounded-full bg-primary" />}
          </button>
        ))}
      </div>

      {selected ? (
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex flex-none items-center gap-3 border-b border-line bg-surface px-4 py-4 md:px-6">
            <div className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-full bg-soft text-[13px] font-bold text-primary">
              {selected.client_initials}
            </div>
            <div className="flex-1">
              <div className="text-[15px] font-bold">{selected.client_name}</div>
              <div className="text-xs text-muted">{selected.topic} · paid consult · ₹350 to you</div>
            </div>
            <button className="whitespace-nowrap rounded-full bg-success-text px-[18px] py-2.5 text-[13px] font-bold text-primary-foreground">
              Start video call
            </button>
          </div>

          <div ref={scrollRef} className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-5 md:px-6">
            {selected.messages.map((m) =>
              m.sender === 'client' ? (
                <div
                  key={m.id}
                  className="max-w-[80%] self-start rounded-[6px_18px_18px_18px] border border-line bg-surface px-4 py-3 text-sm leading-[1.55] sm:max-w-[65%]"
                >
                  {m.text}
                </div>
              ) : (
                <div
                  key={m.id}
                  className="max-w-[80%] self-end rounded-[18px_18px_6px_18px] bg-success-text px-4 py-3 text-sm leading-[1.55] text-white sm:max-w-[65%]"
                >
                  {m.text}
                </div>
              ),
            )}
          </div>

          <div className="flex flex-none gap-2.5 border-t border-line bg-surface px-4 py-4 md:px-6">
            <input
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendReply()}
              placeholder={`Reply to ${selected.client_name}…`}
              className="flex-1 rounded-full border border-line bg-surface px-[18px] py-3"
            />
            <button
              onClick={sendReply}
              disabled={sending}
              className="rounded-full bg-success-text px-6 py-3 text-sm font-bold text-white disabled:opacity-60"
            >
              Reply
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center text-sm text-muted">
          Select a conversation.
        </div>
      )}
    </div>
  )
}
