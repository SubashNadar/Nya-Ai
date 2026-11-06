import { useLocation, useNavigate } from 'react-router-dom'
import {
  CalendarCheck,
  LayoutDashboard,
  type LucideIcon,
  MessageSquareText,
  MessagesSquare,
  Scale,
  UserRound,
} from 'lucide-react'
import { motion } from 'motion/react'
import { useAuth } from '../context/AuthContext'

interface Tab {
  label: string
  path: string
  match: string[]
  icon: LucideIcon
}

// Lawyer-role mobile tabs are a documented default (no source in the demo covers mobile+lawyer) —
// see docs/DECISIONS.md.
const USER_TABS: Tab[] = [
  { label: 'Chat', path: '/chat', match: ['/chat'], icon: MessageSquareText },
  {
    label: 'Lawyers',
    path: '/lawyers',
    match: ['/lawyers', '/plan', '/booking', '/pay', '/success'],
    icon: Scale,
  },
  { label: 'Bookings', path: '/bookings', match: ['/bookings', '/call'], icon: CalendarCheck },
  { label: 'Profile', path: '/account', match: ['/account'], icon: UserRound },
]

const LAWYER_TABS: Tab[] = [
  { label: 'Dashboard', path: '/portal', match: ['/portal', '/call'], icon: LayoutDashboard },
  { label: 'Messages', path: '/messages', match: ['/messages'], icon: MessagesSquare },
  { label: 'Profile', path: '/profile', match: ['/profile'], icon: UserRound },
]

export function BottomTabBar() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const tabs = user?.role === 'lawyer' ? LAWYER_TABS : USER_TABS

  return (
    <nav className="flex flex-none border-t border-line bg-surface px-1.5 pb-3.5 pt-2 md:hidden">
      {tabs.map((tab) => {
        const active = tab.match.some((m) => location.pathname === m || location.pathname.startsWith(m + '/'))
        return (
          <button
            key={tab.label}
            onClick={() => navigate(tab.path)}
            className="flex flex-1 flex-col items-center gap-1 border-none bg-transparent py-1.5"
          >
            <span className="relative h-1 w-[26px]">
              {active && (
                <motion.span
                  layoutId="tab-indicator"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  className="absolute inset-0 rounded-full bg-primary shadow-[0_0_12px_rgba(217,181,110,0.7)]"
                />
              )}
            </span>
            <motion.span
              animate={active ? { scale: 1.12, y: -1 } : { scale: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 420, damping: 22 }}
            >
              <tab.icon
                className={`size-5 ${active ? 'text-primary' : 'text-faint'}`}
                strokeWidth={active ? 2.4 : 2}
              />
            </motion.span>
            <span className={`text-[11px] ${active ? 'font-bold text-ink' : 'font-medium text-faint'}`}>
              {tab.label}
            </span>
          </button>
        )
      })}
    </nav>
  )
}
