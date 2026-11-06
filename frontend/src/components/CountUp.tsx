import { useEffect, useRef, useState } from 'react'
import { animate, useInView, useReducedMotion } from 'motion/react'

/** A number that counts up from zero the first time it scrolls into view. */
export function CountUp({
  value,
  decimals = 0,
  prefix = '',
  suffix = '',
  locale = 'en-IN',
}: {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  locale?: string
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const reduced = useReducedMotion()
  const [shown, setShown] = useState(reduced ? value : 0)

  useEffect(() => {
    if (!inView || reduced) {
      if (reduced) setShown(value)
      return
    }
    const controls = animate(0, value, { duration: 1.1, ease: [0.2, 0.8, 0.2, 1], onUpdate: setShown })
    return () => controls.stop()
  }, [inView, reduced, value])

  return (
    <span ref={ref} className="tabular-nums">
      {prefix}
      {shown.toLocaleString(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  )
}
