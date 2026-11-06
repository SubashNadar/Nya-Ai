import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { BrandLockup } from './Logo'

const LINKS = [
  { to: '/legal', label: 'LEGAL' },
  { to: '/about', label: 'ABOUT' },
  { to: '/contact', label: 'CONTACT' },
  { to: '/help', label: 'HELP' },
]

// Public pages (legal, about, contact, help). Reachable signed in or out, so they sit outside AppShell.
export function InfoLayout() {
  const { user } = useAuth()
  const back = user ? { to: user.role === 'lawyer' ? '/portal' : '/chat', label: 'Back to app' } : { to: '/login', label: 'Sign in' }

  return (
    <div className="min-h-[100dvh] text-ink">
      <header className="sticky top-0 z-20 border-b border-line bg-navy-950/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1120px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 md:px-8">
          <Link to={back.to} aria-label="Nya-AI home">
            <BrandLockup inverted />
          </Link>
          <nav aria-label="Information pages" className="order-3 flex w-full gap-1 overflow-x-auto md:order-none md:w-auto">
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 font-mono text-[11.5px] tracking-[0.12em] transition-colors ${
                    isActive ? 'bg-primary/15 text-primary' : 'text-muted hover:text-ink'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex-1" />
          <Link
            to={back.to}
            className="rounded-full border border-primary/50 px-4 py-1.5 text-[13px] font-semibold text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
          >
            {back.label}
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-[1120px] px-4 py-8 md:px-8 md:py-12">
        <Outlet />
      </main>
      <footer className="border-t border-line px-4 py-6 text-center font-mono text-[11px] tracking-[0.08em] text-faint">
        NYA-AI · LEGAL INFORMATION, NOT LEGAL ADVICE · EMERGENCY 112
      </footer>
    </div>
  )
}

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div className="font-mono text-[11px] tracking-[0.14em] text-primary">{children}</div>
}

export function Panel({ className = '', children }: { className?: string; children: React.ReactNode }) {
  return <section className={`rounded-2xl border border-line bg-surface/90 p-5 md:p-6 ${className}`}>{children}</section>
}
