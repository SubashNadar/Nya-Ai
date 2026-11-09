import animate from 'tailwindcss-animate'

// A theme colour that keeps Tailwind's opacity modifiers (bg-brass/10) working.
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Theme tokens are CSS variables (src/index.css): Ivory light by default, Orbit navy under
        // [data-theme="dark"]. Brand navy (navy-*) is fixed in both themes.
        primary: { DEFAULT: v('primary'), hover: v('primary-hover'), foreground: v('primary-fg') },
        background: v('background'),
        foreground: v('foreground'),
        border: v('border'),
        input: v('input'),
        ring: v('ring'),
        secondary: { DEFAULT: v('secondary'), foreground: v('secondary-fg') },
        accent: { DEFAULT: v('secondary'), foreground: v('secondary-fg') },
        destructive: { DEFAULT: v('destructive'), foreground: '#FFFFFF' },
        popover: { DEFAULT: v('popover'), foreground: v('popover-fg') },
        navy: { 950: '#070F1C', 900: '#0A1424', 800: '#0F1E33', 700: '#162A47', 600: '#1F3A5F' },
        brass: { DEFAULT: v('brass'), light: v('brass-light'), soft: v('brass-soft'), dark: v('brass-dark') },
        soft: v('soft'),
        line: v('line'),
        ink: v('ink'),
        muted: v('muted'),
        bg: v('bg'),
        surface: v('surface'),
        success: { text: v('success-text'), bg: v('success-bg'), dark: v('success-dark'), border: v('success-border') },
        warn: { text: v('warn-text'), bg: v('warn-bg'), border: v('warn-border') },
        focus: v('focus'),
        faint: v('faint'),
        body2: v('body2'),
        body3: v('body3'),
        scrollbar: v('scrollbar'),
        fg: v('fg'),
        display: v('display'),
        info: v('info'),
        danger: v('danger'),
        well: v('well'), // inset panels and form fields
      },
      fontFamily: {
        heading: ['Fraunces', 'Georgia', 'serif'],
        body: ['Figtree', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        lift: 'var(--shadow-lift)',
        composer: 'var(--shadow-composer)',
      },
      keyframes: {
        dotpulse: {
          '0%, 80%, 100%': { opacity: '0.25', transform: 'translateY(0)' },
          '40%': { opacity: '1', transform: 'translateY(-3px)' },
        },
        spin: {
          to: { transform: 'rotate(360deg)' },
        },
        shimmer: {
          from: { backgroundPosition: '200% 0' },
          to: { backgroundPosition: '-200% 0' },
        },
      },
      animation: {
        dotpulse: 'dotpulse 1s infinite',
        shimmer: 'shimmer 2.4s linear infinite',
        spin: 'spin 0.8s linear infinite',
      },
    },
  },
  plugins: [animate],
}
