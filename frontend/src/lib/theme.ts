// Light (Ivory) is the default; the Orbit navy theme is an optional dark mode chosen in Account.
// The choice is a per-device convenience, so storage failures (private mode) just mean light.

export type Theme = 'light' | 'dark'

const KEY = 'nya_ai_theme'

export function getTheme(): Theme {
  try {
    return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

export function applyTheme(theme: Theme): void {
  if (theme === 'dark') document.documentElement.dataset.theme = 'dark'
  else delete document.documentElement.dataset.theme
}

export function setTheme(theme: Theme): void {
  applyTheme(theme)
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    // storage blocked: the theme still applies for this visit
  }
}
