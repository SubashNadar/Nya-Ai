/**
 * App-wide interaction effects, installed once from main.tsx. Pure DOM, no React re-renders:
 * - spotlight: cards (`.bg-surface`, `[data-spot]`) get a soft brass glow that follows the pointer;
 * - tilt: elements with `data-tilt` lean a few degrees toward the pointer;
 * - ripple: rounded buttons get an ink ripple from the press point.
 * Everything is skipped when the user prefers reduced motion. Styles live in index.css (`fx-*`).
 */

const SPOT = '.bg-surface, [data-spot]'

export function installFx(): void {
  if (typeof window === 'undefined') return
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
  let tilted: HTMLElement | null = null

  window.addEventListener(
    'pointermove',
    (e) => {
      if (reduced.matches || e.pointerType === 'touch') return
      const target = e.target as Element | null
      const card = target?.closest<HTMLElement>(SPOT)
      if (card) {
        const r = card.getBoundingClientRect()
        card.style.setProperty('--mx', `${e.clientX - r.left}px`)
        card.style.setProperty('--my', `${e.clientY - r.top}px`)
      }
      const tilt = target?.closest<HTMLElement>('[data-tilt]') ?? null
      if (tilted && tilted !== tilt) tilted.style.transform = ''
      tilted = tilt
      if (tilt) {
        const r = tilt.getBoundingClientRect()
        const x = (e.clientX - r.left) / r.width - 0.5
        const y = (e.clientY - r.top) / r.height - 0.5
        tilt.style.transform = `perspective(900px) rotateX(${(-y * 5).toFixed(2)}deg) rotateY(${(x * 6).toFixed(2)}deg) translateY(-3px)`
      }
    },
    { passive: true },
  )

  window.addEventListener('pointerdown', (e) => {
    if (reduced.matches) return
    const btn = (e.target as Element | null)?.closest<HTMLElement>('button.rounded-full, a.rounded-full')
    if (!btn || (btn as HTMLButtonElement).disabled) return
    const r = btn.getBoundingClientRect()
    const size = Math.max(r.width, r.height) * 2.2
    const ink = document.createElement('span')
    ink.className = 'fx-ripple'
    ink.style.width = ink.style.height = `${size}px`
    ink.style.left = `${e.clientX - r.left - size / 2}px`
    ink.style.top = `${e.clientY - r.top - size / 2}px`
    btn.appendChild(ink)
    ink.addEventListener('animationend', () => ink.remove())
  })
}
