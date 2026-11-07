import type { MouseEvent } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Check, Monitor, Moon, Palette, Sun } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { THEMES, useTheme, type Mode } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

const at = (e: MouseEvent) => ({ x: e.clientX, y: e.clientY })

/** One-click light/dark flip with an animated sun/moon icon. */
export function ModeToggle() {
  const { resolved, setMode } = useTheme()
  const next = resolved === 'dark' ? 'light' : 'dark'
  return (
    <Tooltip>
      <TooltipTrigger
        render={<Button variant="outline" size="icon" aria-label={`Switch to ${next} mode`} className="glass relative overflow-hidden rounded-full" />}
        onClick={(e: MouseEvent) => setMode(next, at(e))}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={resolved}
            initial={{ y: 18, rotate: -90, opacity: 0 }}
            animate={{ y: 0, rotate: 0, opacity: 1 }}
            exit={{ y: -18, rotate: 90, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 22 }}
            className="grid place-items-center"
          >
            {resolved === 'dark' ? <Moon className="size-4" /> : <Sun className="size-4 text-warn" />}
          </motion.span>
        </AnimatePresence>
      </TooltipTrigger>
      <TooltipContent>Switch to {next} mode</TooltipContent>
    </Tooltip>
  )
}

const MODES: { id: Mode; label: string; Icon: typeof Sun }[] = [
  { id: 'light', label: 'Light', Icon: Sun },
  { id: 'dark', label: 'Dark', Icon: Moon },
  { id: 'system', label: 'System', Icon: Monitor },
]

/** Popover with the mode segmented control and the six palette swatches. */
export function ThemePicker() {
  const { mode, theme, setMode, setTheme } = useTheme()

  return (
    <Popover>
      <PopoverTrigger render={<Button variant="outline" size="icon" aria-label="Appearance" className="glass rounded-full" />}>
        <motion.span whileHover={{ rotate: 25 }} className="grid place-items-center">
          <Palette className="size-4" />
        </motion.span>
      </PopoverTrigger>
      <PopoverContent align="end" className="glass w-80 p-4">
        <p className="mb-1 text-sm font-semibold">Appearance</p>
        <p className="mb-3 text-xs text-muted-foreground">Saved on this device.</p>

        <div role="radiogroup" aria-label="Colour mode" className="mb-5 grid grid-cols-3 gap-1 rounded-xl bg-muted p-1">
          {MODES.map(({ id, label, Icon }) => (
            <button
              key={id}
              role="radio"
              aria-checked={mode === id}
              onClick={(e) => setMode(id, at(e))}
              className={cn('relative flex items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-colors', mode === id ? 'text-foreground' : 'text-muted-foreground hover:text-foreground')}
            >
              {mode === id && <motion.span layoutId="mode-pill" className="absolute inset-0 rounded-lg bg-background shadow-sm ring-1 ring-foreground/10" transition={{ type: 'spring', stiffness: 420, damping: 32 }} />}
              <Icon className="relative size-3.5" />
              <span className="relative">{label}</span>
            </button>
          ))}
        </div>

        <p className="mb-2 text-xs font-medium text-muted-foreground">Theme</p>
        <div role="radiogroup" aria-label="Theme" className="grid grid-cols-3 gap-2">
          {THEMES.map((t, i) => {
            const active = theme === t.id
            return (
              <motion.button
                key={t.id}
                role="radio"
                aria-checked={active}
                aria-label={t.label}
                onClick={(e) => setTheme(t.id, at(e))}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.95 }}
                className={cn('group relative overflow-hidden rounded-xl p-2 text-left ring-1 transition-shadow', active ? 'ring-2 ring-primary' : 'ring-foreground/10 hover:ring-foreground/25')}
              >
                {/* mini preview of the palette: gradient header, two "bars" and an accent dot */}
                <div className="relative h-12 overflow-hidden rounded-lg" style={{ background: `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})` }}>
                  <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/30 to-transparent group-hover:animate-shimmer" />
                  <div className="absolute bottom-1.5 left-1.5 space-y-1">
                    <div className="h-1 w-8 rounded bg-white/70" />
                    <div className="h-1 w-5 rounded bg-white/45" />
                  </div>
                  <AnimatePresence>
                    {active && (
                      <motion.span
                        initial={{ scale: 0, rotate: -45 }}
                        animate={{ scale: 1, rotate: 0 }}
                        exit={{ scale: 0 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 20 }}
                        className="absolute right-1.5 top-1.5 grid size-5 place-items-center rounded-full bg-white text-black shadow"
                      >
                        <Check className="size-3" strokeWidth={3} />
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
                <p className="mt-1.5 text-xs font-medium">{t.label}</p>
              </motion.button>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
