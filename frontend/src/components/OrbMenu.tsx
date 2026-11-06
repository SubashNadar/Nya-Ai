import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  CalendarCheck,
  CircleUserRound,
  GitCommitHorizontal,
  LibraryBig,
  LayoutDashboard,
  LogOut,
  type LucideIcon,
  MessageSquareText,
  MessagesSquare,
  Scale,
  UserRound,
} from 'lucide-react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { useAuth } from '../context/AuthContext'
import { LogoMark } from './Logo'

interface Satellite {
  label: string
  path: string
  match: string[]
  icon: LucideIcon
  badge?: number
}

function useSatellites(unreadThreads: number): Satellite[] {
  const { user } = useAuth()
  if (user?.role === 'lawyer') {
    return [
      { label: 'Dashboard', path: '/portal', match: ['/portal', '/call'], icon: LayoutDashboard },
      { label: 'Messages', path: '/messages', match: ['/messages'], icon: MessagesSquare, badge: unreadThreads },
      { label: 'Law library', path: '/library', match: ['/library'], icon: LibraryBig },
      { label: 'Profile', path: '/profile', match: ['/profile'], icon: UserRound },
    ]
  }
  return [
    { label: 'Ask Nya-AI', path: '/chat', match: ['/chat'], icon: MessageSquareText },
    { label: 'My matters', path: '/dashboard', match: ['/dashboard'], icon: GitCommitHorizontal },
    {
      label: 'Advocates',
      path: '/lawyers',
      match: ['/lawyers', '/plan', '/booking', '/pay', '/success'],
      icon: Scale,
    },
    { label: 'Consultations', path: '/bookings', match: ['/bookings', '/call'], icon: CalendarCheck },
    { label: 'Account', path: '/account', match: ['/account'], icon: CircleUserRound },
  ]
}

const isOn = (s: Satellite, pathname: string) => s.match.some((m) => pathname === m || pathname.startsWith(m + '/'))

/**
 * The app's menu: the Nya-AI logo is an orb; tapping it fans the sections out along its orbit.
 * Replaces the sidebar and the phone tab bar (owner's choice, 2026-11-06).
 */
export function OrbBar({ unreadThreads }: { unreadThreads: number }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const reduce = useReducedMotion()
  const satellites = useSatellites(unreadThreads)
  const [open, setOpen] = useState(false)
  const firstRef = useRef<HTMLButtonElement>(null)
  const orbRef = useRef<HTMLButtonElement>(null)
  const current = satellites.find((s) => isOn(s, pathname))
  const unread = satellites.reduce((n, s) => n + (s.badge ?? 0), 0)

  useEffect(() => setOpen(false), [pathname])
  useEffect(() => {
    if (!open) return
    firstRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        orbRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  // Satellites sit on one orbit, spaced evenly downwards so each label (to its right) clears the
  // satellite below it; the arc runs from just under the header round to straight below the orb.
  const many = satellites.length > 3
  const radius = many ? 212 : 170
  const step = many ? 42 : 50
  const place = (i: number) => {
    const y = Math.min(radius, step * (i + 1) - (many ? 2 : 0))
    return { x: Math.round(Math.sqrt(radius * radius - y * y)), y }
  }

  return (
    <>
      <header className="relative z-50 flex h-[60px] flex-none items-center gap-3 border-b border-line bg-navy-950/85 px-3 backdrop-blur md:px-5">
        <div className="relative size-11 flex-none">
          <button
            ref={orbRef}
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-controls="orb-menu"
            aria-label={open ? 'Close menu' : 'Open menu'}
            className={`fx-orb relative grid size-11 place-items-center rounded-full ${open ? 'fx-orb-open' : ''}`}
          >
            <LogoMark size={34} tone="brass" />
            {!open && unread > 0 && (
              <span className="absolute -right-0.5 -top-0.5 grid size-4 place-items-center rounded-full bg-primary text-[9px] font-bold text-primary-foreground">
                {unread}
              </span>
            )}
          </button>
          <AnimatePresence>
            {open && (
              <motion.ul
                id="orb-menu"
                aria-label="Sections"
                className="absolute left-1/2 top-1/2 m-0 list-none p-0"
                initial="closed"
                animate="open"
                exit="closed"
              >
                {/* the orbit the satellites ride on */}
                <motion.li
                  aria-hidden
                  variants={{ closed: { opacity: 0, scale: 0.3 }, open: { opacity: 1, scale: 1 } }}
                  transition={{ duration: reduce ? 0 : 0.35 }}
                  className="pointer-events-none absolute rounded-full border border-dashed border-brass/30"
                  style={{ width: radius * 2, height: radius * 2, left: -radius, top: -radius }}
                />
                {satellites.map((s, i) => {
                  const { x, y } = place(i)
                  const on = isOn(s, pathname)
                  return (
                    <motion.li
                      key={s.path}
                      className="absolute"
                      style={{ left: 0, top: 0 }}
                      variants={{
                        closed: { x: 0, y: 0, opacity: 0, scale: 0.4 },
                        open: { x, y, opacity: 1, scale: 1 },
                      }}
                      transition={
                        reduce
                          ? { duration: 0 }
                          : { type: 'spring', stiffness: 420, damping: 26, delay: 0.035 * i }
                      }
                    >
                      <button
                        ref={i === 0 ? firstRef : undefined}
                        onClick={() => navigate(s.path)}
                        aria-current={on ? 'page' : undefined}
                        className="group absolute -left-[23px] -top-[23px] flex items-center"
                      >
                        <span
                          className={`relative grid size-[46px] flex-none place-items-center rounded-full border shadow-lift transition-colors ${
                            on
                              ? 'border-brass bg-primary text-primary-foreground'
                              : 'border-white/15 bg-navy-800 text-white group-hover:border-brass/60 group-hover:text-brass-light'
                          }`}
                        >
                          <s.icon className="size-[19px]" strokeWidth={on ? 2.3 : 1.9} />
                          {!!s.badge && (
                            <span className="absolute -right-1 -top-1 grid size-[18px] place-items-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground ring-2 ring-navy-950">
                              {s.badge}
                            </span>
                          )}
                        </span>
                        <span
                          className={`ml-2 whitespace-nowrap rounded-full border px-2.5 py-1 font-mono text-[11px] tracking-[0.1em] backdrop-blur ${
                            on
                              ? 'border-brass/50 bg-navy-950/80 text-brass-light'
                              : 'border-white/10 bg-navy-950/70 text-white/80 group-hover:text-white'
                          }`}
                        >
                          {s.label.toUpperCase()}
                        </span>
                      </button>
                    </motion.li>
                  )
                })}
                <motion.li
                  className="absolute w-[230px]"
                  style={{ left: -18, top: radius + 44 }}
                  variants={{ closed: { opacity: 0, y: -8 }, open: { opacity: 1, y: 0 } }}
                  transition={{ duration: reduce ? 0 : 0.3, delay: reduce ? 0 : 0.2 }}
                >
                  {user?.role === 'user' && (
                    <div className="rounded-2xl border border-brass/30 bg-navy-900/90 px-3.5 py-3 backdrop-blur">
                      <div className="font-heading text-[14px] font-bold text-white">Nya-AI Plus</div>
                      <div className="mt-0.5 text-[12px] leading-snug text-white/65">
                        Unlimited AI chats + 1 free consult every month · <span className="font-semibold text-brass-light">₹299/month</span>
                      </div>
                    </div>
                  )}
                  <nav
                    aria-label="Information pages"
                    className="mt-3 flex flex-wrap gap-x-3 gap-y-1 px-1 font-mono text-[10.5px] tracking-[0.1em] text-white/55"
                  >
                    <Link to="/help" className="hover:text-brass-light">HELP</Link>
                    <Link to="/contact" className="hover:text-brass-light">CONTACT</Link>
                    <Link to="/legal" className="hover:text-brass-light">LEGAL</Link>
                    <Link to="/about" className="hover:text-brass-light">ABOUT</Link>
                  </nav>
                </motion.li>
              </motion.ul>
            )}
          </AnimatePresence>
        </div>

        <button onClick={() => setOpen((o) => !o)} className="flex min-w-0 flex-col items-start leading-none" tabIndex={-1}>
          <span className="font-display text-[20px] font-semibold leading-none text-brass-soft">
            Nya<span className="font-mono text-[14px] text-brass-light">·AI</span>
          </span>
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={current?.label ?? 'none'}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: reduce ? 0 : 0.2 }}
              className="mt-[5px] truncate font-mono text-[10.5px] tracking-[0.14em] text-white/55"
            >
              § {(current?.label ?? 'Indian law, cited').toUpperCase()}
            </motion.span>
          </AnimatePresence>
        </button>

        <div className="flex-1" />

        <div className="flex items-center gap-2.5 rounded-full border border-white/10 bg-white/5 py-1 pl-1 pr-1.5">
          <div className="grid size-8 flex-none place-items-center rounded-full bg-gradient-to-br from-brass-light to-brass-dark text-[12px] font-bold text-navy-950">
            {user?.initials ?? '?'}
          </div>
          <div className="hidden min-w-0 sm:block">
            <div className="max-w-[140px] truncate text-[12.5px] font-semibold leading-tight text-white">{user?.name ?? ''}</div>
            <div className="text-[10.5px] leading-tight text-white/45">{user?.role === 'lawyer' ? 'Advocate' : 'Member'}</div>
          </div>
          <button
            onClick={logout}
            aria-label="Sign out"
            title="Sign out"
            className="rounded-full p-1.5 text-white/50 transition-colors hover:bg-white/10 hover:text-white"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </header>

      <AnimatePresence>
        {open && (
          <motion.div
            aria-hidden
            onClick={() => setOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.25 }}
            className="fixed inset-0 z-40 bg-navy-950/65 backdrop-blur-[3px]"
          />
        )}
      </AnimatePresence>
    </>
  )
}
