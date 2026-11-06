import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Clock3, IndianRupee, type LucideIcon, Scale, Sparkles } from 'lucide-react'
import { motion } from 'motion/react'
import { BrandLockup } from '../components/Logo'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../lib/api'
import type { Role } from '../types'

const BADGES: { label: string; icon: LucideIcon }[] = [
  { label: 'Free AI answers', icon: Sparkles },
  { label: 'Consults from ₹500', icon: IndianRupee },
  { label: '24×7, on your phone', icon: Clock3 },
]

export default function LoginPage() {
  const navigate = useNavigate()
  const { requestOtp, verifyOtp, guestLogin } = useAuth()

  const [role, setRole] = useState<Role>('user')
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loginSub = role === 'lawyer' ? 'Sign in to your lawyer portal' : 'Sign in with your mobile number'
  const guestLabel = role === 'lawyer' ? 'Explore as demo lawyer →' : 'Explore as guest →'

  function afterLogin(userRole: Role) {
    navigate(userRole === 'lawyer' ? '/portal' : '/chat', { replace: true })
  }

  async function handleSendOtp() {
    if (!phone.trim()) {
      setError('Enter a mobile number first.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      await requestOtp(phone.trim())
      setOtpSent(true)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleVerifyOtp() {
    if (!/^\d{4}$/.test(otp.trim())) {
      setError('Enter the 4-digit OTP.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const user = await verifyOtp(phone.trim(), otp.trim(), role)
      afterLogin(user.role)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleGuestLogin() {
    setError(null)
    setLoading(true)
    try {
      const user = await guestLogin(role)
      afterLogin(user.role)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[100dvh] bg-bg font-body text-ink">
      <div className="relative hidden w-[46%] flex-none flex-col justify-between overflow-hidden bg-navy-950 p-12 text-white lg:flex">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] [background-size:44px_44px] [mask-image:radial-gradient(ellipse_at_top_left,black,transparent_75%)]"
        />
        <div aria-hidden className="pointer-events-none absolute -left-24 top-1/3 h-80 w-80 rounded-full bg-navy-600/50 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute -bottom-24 right-0 h-72 w-72 rounded-full bg-brass/25 blur-3xl" />
        <div className="relative">
          <BrandLockup inverted />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="relative max-w-[460px]"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-brass/40 bg-brass/10 px-3 py-1 text-xs font-semibold text-brass-light">
            <Scale className="size-3.5" />
            AI legal assistant for India
          </div>
          <h1 className="mt-5 font-display text-[44px] font-semibold leading-[1.05] tracking-[-0.02em] xl:text-[52px]">
            Legal help, finally <span className="italic text-brass-light">within reach.</span>
          </h1>
          <p className="mt-5 text-[16px] leading-[1.7] text-white/70">
            90% of Indians can't afford a lawyer. Ask Nya-AI anything about your rights — free, instant,
            24×7. Talk to a verified lawyer only when you need one, from ₹500.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3">
            {BADGES.map((b) => (
              <div key={b.label} className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
                <b.icon className="size-5 text-brass-light" />
                <div className="mt-3 text-[13px] font-semibold leading-snug text-white/90">{b.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
        <div className="relative rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-white/45">
            <Sparkles className="size-3.5 text-brass-light" />
            Ask Nya-AI
          </div>
          <div className="mt-3 ml-auto w-fit rounded-2xl rounded-tr-md bg-white/10 px-3.5 py-2 text-[13px]">
            How do I file an FIR?
          </div>
          <div className="mt-2 w-fit max-w-[90%] rounded-2xl rounded-tl-md bg-brass-soft px-3.5 py-2.5 text-[13px] leading-relaxed text-navy-900">
            Filing an FIR is free, and the police are duty-bound to register it.
          </div>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 flex-none items-center px-6 lg:hidden">
          <BrandLockup inverted />
        </header>
        <div className="flex flex-1 items-center justify-center p-6">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut', delay: 0.1 }}
            className="w-full max-w-[400px]"
          >
            <div className="mb-8 lg:hidden">
              <h1 className="font-display text-[34px] font-semibold leading-[1.08]">
                Legal help, finally <span className="italic text-primary">within reach.</span>
              </h1>
            </div>
              <div className="font-display text-[30px] font-semibold tracking-[-0.01em]">Get started</div>
              <div className="mt-5 flex gap-1 rounded-full border border-line bg-bg p-1">
                <button
                  onClick={() => setRole('user')}
                  className={`flex-1 rounded-full px-2.5 py-2 text-[13px] font-semibold transition-colors ${
                    role === 'user' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-body2 hover:text-ink'
                  }`}
                >
                  I need legal help
                </button>
                <button
                  onClick={() => setRole('lawyer')}
                  className={`flex-1 rounded-full px-2.5 py-2 text-[13px] font-semibold transition-colors ${
                    role === 'lawyer' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-body2 hover:text-ink'
                  }`}
                >
                  I'm a lawyer
                </button>
              </div>
              <div className="mt-3 text-[13px] text-muted">{loginSub}</div>

              <div className="mt-[18px] text-[13px] font-semibold">Mobile number</div>
              <div className="mt-1.5 flex gap-2">
                <div className="flex items-center rounded-xl border border-line bg-bg px-3.5 py-3 text-sm font-semibold">
                  +91
                </div>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                  placeholder="98765 43210"
                  inputMode="numeric"
                  className="flex-1 rounded-xl border border-line bg-surface px-3.5 py-3 text-sm transition-shadow focus:border-focus focus:outline-none focus:ring-4 focus:ring-soft"
                />
              </div>

              {otpSent ? (
                <>
                  <div className="mt-3.5 text-[13px] font-semibold">
                    Enter OTP <span className="font-medium text-muted">(demo: 1234)</span>
                  </div>
                  <input
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="• • • •"
                    inputMode="numeric"
                    className="mt-1.5 w-full rounded-xl border border-line bg-surface px-3.5 py-3 text-lg tracking-[8px] transition-shadow focus:border-focus focus:outline-none focus:ring-4 focus:ring-soft"
                  />
                  <button
                    onClick={handleVerifyOtp}
                    disabled={loading}
                    className="mt-3.5 w-full rounded-full bg-primary hover:bg-primary-hover py-3.5 text-[15px] font-bold text-primary-foreground shadow-card transition-all hover:shadow-lift disabled:opacity-60"
                  >
                    {loading ? 'Verifying…' : 'Continue'}
                  </button>
                </>
              ) : (
                <button
                  onClick={handleSendOtp}
                  disabled={loading}
                  className="mt-4 w-full rounded-full bg-primary hover:bg-primary-hover py-3.5 text-[15px] font-bold text-primary-foreground shadow-card transition-all hover:shadow-lift disabled:opacity-60"
                >
                  {loading ? 'Sending…' : 'Get OTP'}
                </button>
              )}

              {error && <div className="mt-3 text-[12px] font-medium text-warn-text">{error}</div>}

              <div className="my-4 flex items-center gap-2.5">
                <div className="h-px flex-1 bg-line" />
                <div className="text-xs text-muted">or</div>
                <div className="h-px flex-1 bg-line" />
              </div>
              <button
                onClick={handleGuestLogin}
                disabled={loading}
                className="w-full rounded-full border border-line bg-surface py-3 text-sm font-semibold text-ink transition-colors hover:border-focus hover:bg-soft disabled:opacity-60"
              >
                {guestLabel}
              </button>
            <div className="mt-5 text-[11.5px] leading-relaxed text-faint">
              By continuing you agree to our{' '}
              <Link to="/legal#terms" className="text-primary hover:underline">
                Terms
              </Link>{' '}
              and{' '}
              <Link to="/legal#privacy" className="text-primary hover:underline">
                Privacy notice
              </Link>
              . Nya-AI gives legal information, not legal advice.
            </div>
            <nav aria-label="Information pages" className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] tracking-[0.1em] text-muted">
              <Link to="/about" className="hover:text-primary">ABOUT</Link>
              <Link to="/contact" className="hover:text-primary">CONTACT</Link>
              <Link to="/help" className="hover:text-primary">HELP</Link>
              <Link to="/legal" className="hover:text-primary">LEGAL</Link>
            </nav>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
