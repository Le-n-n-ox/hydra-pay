import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

export type Mode = 'light' | 'dark' | 'system'
export type ThemeId = 'hydra' | 'emerald' | 'sunset' | 'orchid' | 'aqua' | 'graphite'

/** Swatch colours for the picker (the real palettes live in src/themes.css). */
export const THEMES: { id: ThemeId; label: string; colors: [string, string] }[] = [
  { id: 'hydra', label: 'Hydra', colors: ['oklch(0.62 0.19 262)', 'oklch(0.56 0.19 293)'] },
  { id: 'emerald', label: 'Emerald', colors: ['oklch(0.62 0.15 158)', 'oklch(0.56 0.15 185)'] },
  { id: 'sunset', label: 'Sunset', colors: ['oklch(0.68 0.18 45)', 'oklch(0.6 0.18 15)'] },
  { id: 'orchid', label: 'Orchid', colors: ['oklch(0.64 0.2 335)', 'oklch(0.56 0.2 300)'] },
  { id: 'aqua', label: 'Aqua', colors: ['oklch(0.66 0.14 220)', 'oklch(0.6 0.14 190)'] },
  { id: 'graphite', label: 'Graphite', colors: ['oklch(0.5 0.025 260)', 'oklch(0.35 0.025 260)'] },
]

const STORAGE_KEY = 'hydra-ui'

type Stored = { mode: Mode; theme: ThemeId }

function read(): Stored {
  try {
    const s = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') as Partial<Stored>
    return {
      mode: s.mode === 'light' || s.mode === 'dark' || s.mode === 'system' ? s.mode : 'dark',
      theme: THEMES.some((t) => t.id === s.theme) ? (s.theme as ThemeId) : 'hydra',
    }
  } catch {
    return { mode: 'dark', theme: 'hydra' }
  }
}

const systemDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches

function apply(resolved: 'light' | 'dark', theme: ThemeId) {
  const root = document.documentElement
  root.classList.toggle('dark', resolved === 'dark')
  root.dataset.theme = theme
  root.style.colorScheme = resolved
  const bg = getComputedStyle(root).getPropertyValue('--background').trim()
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', bg || (resolved === 'dark' ? '#0b1020' : '#f7f8fc'))
}

/**
 * Run a DOM change with a circular "reveal" that grows from the click point.
 * Falls back to a short colour cross-fade where View Transitions aren't supported,
 * and to an instant switch when the user prefers reduced motion.
 */
function transition(change: () => void, origin?: { x: number; y: number }) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const doc = document as Document & { startViewTransition?: (cb: () => void) => { ready: Promise<void> } }
  if (reduce) return change()
  if (!doc.startViewTransition) {
    const root = document.documentElement
    root.classList.add('theme-fade')
    change()
    setTimeout(() => root.classList.remove('theme-fade'), 400)
    return
  }
  const x = origin?.x ?? innerWidth / 2
  const y = origin?.y ?? 0
  const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
  const vt = doc.startViewTransition(change)
  vt.ready
    .then(() => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] },
        { duration: 550, easing: 'cubic-bezier(.4,0,.2,1)', pseudoElement: '::view-transition-new(root)' },
      )
    })
    .catch(() => {})
}

type ThemeCtx = {
  mode: Mode
  theme: ThemeId
  resolved: 'light' | 'dark'
  /** Bumps on every visual change, so canvas/SVG consumers (charts) can re-read CSS variables. */
  version: number
  setMode: (m: Mode, origin?: { x: number; y: number }) => void
  setTheme: (t: ThemeId, origin?: { x: number; y: number }) => void
}

const Ctx = createContext<ThemeCtx | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Stored>(read)
  const [sysDark, setSysDark] = useState(systemDark)
  const [version, setVersion] = useState(0)
  const resolved: 'light' | 'dark' = state.mode === 'system' ? (sysDark ? 'dark' : 'light') : state.mode

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const on = () => setSysDark(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  // Keep <html> in sync (the inline script in index.html sets it before first paint).
  useEffect(() => {
    apply(resolved, state.theme)
    setVersion((v) => v + 1)
  }, [resolved, state.theme])

  const current = useRef(state)
  current.current = state

  const update = useCallback((next: Partial<Stored>, origin?: { x: number; y: number }) => {
    const s = { ...current.current, ...next }
    if (s.mode === current.current.mode && s.theme === current.current.theme) return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
    const res = s.mode === 'system' ? (systemDark() ? 'dark' : 'light') : s.mode
    // Paint the new palette inside the transition, then let React catch up.
    transition(() => apply(res, s.theme), origin)
    setState(s)
  }, [])

  const value = useMemo<ThemeCtx>(
    () => ({
      ...state,
      resolved,
      version,
      setMode: (mode, origin) => update({ mode }, origin),
      setTheme: (theme, origin) => update({ theme }, origin),
    }),
    [state, resolved, version, update],
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useTheme() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme must be used inside <ThemeProvider>')
  return ctx
}

/** Current colour values from the active palette, for chart libraries that need real colour strings. */
export function useThemeColors() {
  const { version } = useTheme()
  return useMemo(() => {
    const css = getComputedStyle(document.documentElement)
    const v = (name: string) => css.getPropertyValue(name).trim()
    return {
      chart1: v('--chart-1'),
      chart2: v('--chart-2'),
      chart3: v('--chart-3'),
      brand1: v('--brand-1'),
      brand2: v('--brand-2'),
      good: v('--good'),
      bad: v('--bad'),
      warn: v('--warn'),
      axis: v('--muted-foreground'),
      grid: v('--border'),
      track: v('--muted'),
    }
  }, [version])
}
