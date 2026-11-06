import animate from 'tailwindcss-animate'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Orbit theme: dark navy with a faint brass grid, brass accents, cream highlights.
        primary: {
          DEFAULT: '#D9B56E',
          hover: '#E6C88A',
          foreground: '#0A1424',
        },
        // shadcn/ui token names, mapped onto the Orbit palette
        background: '#0A1424',
        foreground: '#F3F5F9',
        border: '#24364F',
        input: '#2B3F5C',
        ring: '#D9B56E',
        secondary: { DEFAULT: '#162A47', foreground: '#F3F5F9' },
        accent: { DEFAULT: '#162A47', foreground: '#F3F5F9' },
        destructive: { DEFAULT: '#E5484D', foreground: '#FFFFFF' },
        popover: { DEFAULT: '#0F1E33', foreground: '#F3F5F9' },
        navy: {
          950: '#070F1C',
          900: '#0A1424',
          800: '#0F1E33',
          700: '#162A47',
          600: '#1F3A5F',
        },
        brass: {
          DEFAULT: '#B8893B',
          light: '#D9B56E',
          soft: '#F6EEDF',
          dark: '#8C6526',
        },
        soft: '#162A47',
        line: '#24364F',
        ink: '#F3F5F9',
        muted: '#A9B4C4',
        bg: '#0A1424',
        surface: '#0F1E33',
        success: {
          text: '#8FD3B1',
          bg: '#12352B',
          dark: '#5FB98E',
          border: '#1F5543',
        },
        warn: {
          text: '#E8C98A',
          bg: '#2A2214',
          border: '#4A3B1E',
        },
        focus: '#D9B56E',
        faint: '#8592A6',
        body2: '#C9D1DC',
        body3: '#DCE2EA',
        scrollbar: '#2B3F5C',
      },
      fontFamily: {
        heading: ['Fraunces', 'Georgia', 'serif'],
        body: ['Figtree', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        soft: '0 8px 24px rgba(0,0,0,0.35)',
        login: '0 12px 40px rgba(0,0,0,0.4)',
        card: '0 1px 2px rgba(0,0,0,0.25), 0 4px 16px rgba(0,0,0,0.25)',
        lift: '0 2px 4px rgba(0,0,0,0.3), 0 16px 40px rgba(0,0,0,0.45)',
        composer: '0 8px 30px rgba(0,0,0,0.45)',
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
