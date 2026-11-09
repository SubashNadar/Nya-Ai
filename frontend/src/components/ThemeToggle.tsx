import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'
import { getTheme, setTheme, type Theme } from '../lib/theme'

/** Appearance row for Account / Profile: Ivory (light, default) or Orbit navy (dark). */
export default function ThemeToggle() {
  const [theme, setLocal] = useState<Theme>(getTheme)
  const dark = theme === 'dark'

  function toggle() {
    const next: Theme = dark ? 'light' : 'dark'
    setTheme(next)
    setLocal(next)
  }

  return (
    <div className="flex max-w-[480px] items-center justify-between gap-4 rounded-[20px] border border-line bg-surface px-5 py-3.5">
      <div className="flex items-center gap-3">
        {dark ? <Moon className="size-[18px] text-brass-light" /> : <Sun className="size-[18px] text-brass-light" />}
        <div>
          <div className="text-sm font-semibold text-ink">Dark mode</div>
          <div className="text-[12.5px] text-muted">{dark ? 'Orbit navy' : 'Ivory (default)'}</div>
        </div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={dark}
        aria-label="Dark mode"
        onClick={toggle}
        className={`relative h-6 w-11 flex-none rounded-full border transition-colors ${
          dark ? 'border-brass bg-brass' : 'border-line bg-well'
        }`}
      >
        <span
          aria-hidden
          className={`absolute top-1/2 size-[18px] -translate-y-1/2 rounded-full bg-surface shadow-card transition-all ${
            dark ? 'left-[22px]' : 'left-[2px]'
          }`}
        />
      </button>
    </div>
  )
}
