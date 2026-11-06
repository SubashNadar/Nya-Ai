// Nya-AI mark: scales of justice inside a dashed orbit ring, with a satellite dot.
export function LogoMark({ size = 38, tone = 'navy' }: { size?: number; tone?: 'navy' | 'brass' }) {
  const stroke = tone === 'brass' ? '#D9B56E' : '#1F3A5F'
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      stroke={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="flex-shrink-0"
    >
      <circle cx="32" cy="32" r="28" strokeWidth="2" strokeDasharray="2.5 3.5" />
      <circle cx="51.8" cy="12.2" r="4" fill={stroke} stroke="none" />
      <path d="M32 15v31M19 21.5h26M24 47h16" strokeWidth="3.2" />
      <path d="M15 32.5a6 3.6 0 0 0 12 0zM37 32.5a6 3.6 0 0 0 12 0z" strokeWidth="2.6" />
    </svg>
  )
}

export function BrandLockup({ inverted = false }: { inverted?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <LogoMark tone={inverted ? 'brass' : 'navy'} />
      <div className="flex flex-col leading-none">
        <span
          className={`font-display text-[21px] font-semibold leading-none ${inverted ? 'text-brass-soft' : 'text-ink'}`}
        >
          Nya
          <span className={`font-mono text-[15px] ${inverted ? 'text-brass-light' : 'text-brass-dark'}`}>·AI</span>
        </span>
        <span className={`mt-[4px] font-mono text-[10.5px] tracking-[0.12em] ${inverted ? 'text-white/55' : 'text-muted'}`}>
          INDIAN LAW, CITED
        </span>
      </div>
    </div>
  )
}
