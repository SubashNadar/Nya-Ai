import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ThemeToggle from '../components/ThemeToggle'

export default function AccountPage() {
  const { user, logout } = useAuth()

  // Same name rule as DashboardPage.tsx's greeting: the login flow never collects a real name,
  // so this is 'friend' for phone/OTP users and 'Guest' for guest login — not derived from user.name.
  const displayName = user?.phone ? 'friend' : 'Guest'

  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <h1 className="font-heading text-2xl font-extrabold md:text-[28px]">Profile</h1>

      <div className="mt-5 flex max-w-[480px] items-center gap-4 rounded-[20px] border border-line bg-surface p-5">
        <div className="flex h-[52px] w-[52px] flex-none items-center justify-center rounded-full bg-success-text text-[17px] font-bold text-white">
          {user?.initials ?? '?'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[15px] font-bold">{displayName}</div>
          {user?.phone && <div className="mt-0.5 text-[13px] text-muted">+91 {user.phone}</div>}
        </div>
      </div>

      <div className="mt-5">
        <ThemeToggle />
      </div>

      <nav aria-label="Information pages" className="mt-5 max-w-[480px] divide-y divide-line overflow-hidden rounded-[20px] border border-line bg-surface">
        {[
          ['/help', 'Help and quick support'],
          ['/contact', 'Contact us'],
          ['/legal', 'Disclaimer, privacy and terms'],
          ['/about', 'About Nya-AI'],
        ].map(([to, label]) => (
          <Link key={to} to={to} className="flex items-center justify-between px-5 py-3.5 text-sm font-semibold text-ink hover:bg-soft">
            {label}
            <span aria-hidden className="text-primary">›</span>
          </Link>
        ))}
      </nav>

      <button
        onClick={() => logout()}
        className="mt-5 w-full max-w-[480px] rounded-full border border-line bg-surface py-3 text-sm font-semibold text-ink transition-colors hover:bg-bg"
      >
        Sign out
      </button>
    </div>
  )
}
