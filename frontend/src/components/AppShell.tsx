import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { BrandLockup } from './Logo'
import { Sidebar } from './Sidebar'
import { BottomTabBar } from './BottomTabBar'
import { useAuth } from '../context/AuthContext'
import { getMessageThreads } from '../lib/api'

export function AppShell() {
  const { user } = useAuth()
  const [unreadThreads, setUnreadThreads] = useState(0)

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
    <div className="flex h-[100dvh] flex-col overflow-hidden font-body text-ink md:flex-row">
      <header className="flex h-16 flex-none items-center gap-3.5 border-b border-line bg-navy-950/85 px-4 backdrop-blur md:hidden">
        <BrandLockup inverted />
      </header>
      <Sidebar unreadThreads={unreadThreads} />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <main className="flex min-h-0 min-w-0 flex-1 flex-col">
          <Outlet />
        </main>
        <BottomTabBar />
      </div>
    </div>
  )
}
