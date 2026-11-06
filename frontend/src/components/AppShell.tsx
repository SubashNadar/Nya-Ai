import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { motion } from 'motion/react'
import { OrbBar } from './OrbMenu'
import { useAuth } from '../context/AuthContext'
import { getMessageThreads } from '../lib/api'

export function AppShell() {
  const { user } = useAuth()
  const [unreadThreads, setUnreadThreads] = useState(0)
  const { pathname } = useLocation()

  useEffect(() => {
    if (user?.role !== 'lawyer') return
    let cancelled = false
    getMessageThreads()
      .then(({ threads }) => {
        if (!cancelled) setUnreadThreads(threads.filter((t) => t.unread).length)
      })
      .catch(() => {
        if (!cancelled) setUnreadThreads(0)
      })
    return () => {
      cancelled = true
    }
  }, [user?.role])

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden font-body text-ink">
      <OrbBar unreadThreads={unreadThreads} />
      <main className="flex min-h-0 min-w-0 flex-1 flex-col">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 10, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
          className="flex min-h-0 min-w-0 flex-1 flex-col"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
