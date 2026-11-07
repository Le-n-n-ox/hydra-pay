import { useEffect, useRef, type ComponentType, type ReactNode } from 'react'
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from 'motion/react'
import { CheckCircle2, Clock, Inbox, XCircle, type LucideProps } from 'lucide-react'

import { cn } from '@/lib/utils'
import { hue, initials, payLabel, payState } from '@/lib/format'

/* ---------- background: drifting colour orbs over a faint grid ---------- */

export function Background() {
  const reduce = useReducedMotion()
  const orbs = [
    { c: 'bg-brand-1', pos: '-left-40 -top-40', move: { x: [0, 80, 0], y: [0, 50, 0] }, d: 18 },
    { c: 'bg-brand-2', pos: '-right-40 -bottom-48', move: { x: [0, -70, 0], y: [0, -60, 0] }, d: 22 },
    { c: 'bg-brand-3', pos: 'left-1/3 top-1/2', move: { x: [0, 60, -40, 0], y: [0, -40, 30, 0] }, d: 26 },
  ]
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-background">
      {orbs.map((o, i) => (
        <motion.div
          key={i}
          className={cn('absolute size-[34rem] rounded-full opacity-(--orb-opacity) blur-[120px]', o.c, o.pos)}
          animate={reduce ? undefined : o.move}
          transition={{ duration: o.d, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
      <div className="grid-bg absolute inset-0" />
    </div>
  )
}

/* ---------- numbers that count up/down smoothly when they change ---------- */

export function AnimatedNumber({ value, format = (n) => Math.round(n).toLocaleString() }: {
  value: number
  format?: (n: number) => string
}) {
  const mv = useMotionValue(value)
  const text = useTransform(mv, format)
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      mv.set(value)
      return
    }
    const c = animate(mv, value, { duration: 0.8, ease: [0.16, 1, 0.3, 1] })
    return () => c.stop()
  }, [value, mv])
  return <motion.span className="tabular-nums">{text}</motion.span>
}

/* ---------- small pieces ---------- */

export function StatusDot({ on, warn, className }: { on: boolean; warn?: boolean; className?: string }) {
  const color = warn ? 'bg-amber-400' : on ? 'bg-emerald-400' : 'bg-rose-500'
  return (
    <span className={cn('relative inline-flex size-2.5', className)}>
      {(on || warn) && <span className={cn('absolute inset-0 rounded-full animate-ping-slow', color)} />}
      <span className={cn('relative inline-flex size-2.5 rounded-full', color)} />
    </span>
  )
}

export function PersonAvatar({ name, className }: { name: string; className?: string }) {
  const h = hue(name)
  return (
    <span
      className={cn('inline-grid size-9 shrink-0 place-items-center rounded-full text-xs font-semibold text-white ring-2 ring-foreground/10', className)}
      style={{ background: `linear-gradient(135deg, hsl(${h} 70% 55%), hsl(${(h + 40) % 360} 70% 42%))` }}
    >
      {initials(name)}
    </span>
  )
}

const payStyles = {
  paid: { cls: 'bg-emerald-500/15 text-good ring-emerald-500/30', Icon: CheckCircle2 },
  failed: { cls: 'bg-rose-500/15 text-bad ring-rose-500/30', Icon: XCircle },
  waiting: { cls: 'bg-amber-500/15 text-warn ring-amber-500/30', Icon: Clock },
}

export function PaymentBadge({ status }: { status: string }) {
  const st = payState(status)
  const { cls, Icon } = payStyles[st]
  return (
    <span className={cn('inline-flex min-w-0 max-w-[16rem] shrink items-center gap-1.5 truncate rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset', cls)}>
      <Icon className={cn('size-3.5 shrink-0', st === 'waiting' && 'animate-spin [animation-duration:3s]')} />
      <span className="truncate">{payLabel(status)}</span>
    </span>
  )
}

export function Pill({ tone = 'muted', children, className }: {
  tone?: 'green' | 'red' | 'amber' | 'blue' | 'violet' | 'muted'
  children: ReactNode
  className?: string
}) {
  const tones = {
    green: 'bg-emerald-500/15 text-good ring-emerald-500/30',
    red: 'bg-rose-500/15 text-bad ring-rose-500/30',
    amber: 'bg-amber-500/15 text-warn ring-amber-500/30',
    blue: 'bg-brand-1/15 text-brand-text ring-brand-1/30',
    violet: 'bg-brand-2/15 text-brand-text ring-brand-2/30',
    muted: 'bg-foreground/5 text-muted-foreground ring-foreground/10',
  }
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset', tones[tone], className)}>
      {children}
    </span>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, hint }: { icon?: ComponentType<LucideProps>; title: string; hint?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center gap-2 py-12 text-center"
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        className="grid size-14 place-items-center rounded-2xl bg-foreground/5 ring-1 ring-foreground/10"
      >
        <Icon className="size-6 text-muted-foreground" />
      </motion.div>
      <p className="font-medium">{title}</p>
      {hint && <p className="max-w-xs text-sm text-muted-foreground">{hint}</p>}
    </motion.div>
  )
}

/* ---------- panels and stat tiles ---------- */

export const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 26 } },
}

export const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } }

export function Panel({ title, icon: Icon, action, children, className, bodyClassName }: {
  title?: ReactNode
  icon?: ComponentType<LucideProps>
  action?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  return (
    <motion.section variants={fadeUp} className={cn('glass rounded-2xl', className)}>
      {(title || action) && (
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-foreground/[0.06] px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold tracking-tight">
            {Icon && <Icon className="size-4 text-primary" />}
            {title}
          </h2>
          {action}
        </header>
      )}
      <div className={cn('p-5', bodyClassName)}>{children}</div>
    </motion.section>
  )
}

const gradients = {
  green: 'from-emerald-500 to-teal-600 shadow-emerald-500/30',
  blue: 'from-brand-1 to-brand-2 shadow-brand-1/30',
  red: 'from-rose-500 to-red-700 shadow-rose-500/30',
  violet: 'from-brand-2 to-brand-3 shadow-brand-2/30',
  amber: 'from-amber-400 to-orange-600 shadow-amber-500/30',
}

type Icon = ComponentType<LucideProps>

const toneText = {
  green: 'text-good',
  blue: 'text-brand-text',
  red: 'text-bad',
  violet: 'text-brand-text',
  amber: 'text-warn',
}

export type StatMeta = { icon: Icon; label: string; value: ReactNode }

export function StatCard({ icon: Icon, label, value, format, tone, badge, meta, progress, hint, children }: {
  icon: Icon
  label: string
  value: number
  format?: (n: number) => string
  tone: keyof typeof gradients
  /** Small status chip in the top-right corner. `pulse` adds a live dot. */
  badge?: { icon?: Icon; text: string; tone?: 'green' | 'red' | 'amber' | 'blue' | 'violet' | 'muted'; pulse?: boolean }
  /** Breakdown row under the number: each item gets its own icon. */
  meta?: StatMeta[]
  /** 0–1 bar with a caption, e.g. share of taps that were paid. */
  progress?: { value: number; label: string }
  hint?: ReactNode
  children?: ReactNode
}) {
  const BadgeIcon = badge?.icon
  const pct = progress ? Math.max(0, Math.min(1, progress.value || 0)) : 0
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="glass group relative flex flex-col overflow-hidden rounded-2xl p-5"
    >
      {/* accent line, corner glow and a large watermark of the card's icon */}
      <div className={cn('absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r', gradients[tone])} />
      <div className={cn('pointer-events-none absolute -right-10 -top-10 size-32 rounded-full bg-gradient-to-br opacity-10 blur-2xl transition-opacity duration-500 group-hover:opacity-30', gradients[tone])} />
      <Icon
        aria-hidden
        strokeWidth={1.25}
        className={cn('pointer-events-none absolute -bottom-6 -right-6 size-32 opacity-[0.06] transition-all duration-500 group-hover:-rotate-12 group-hover:scale-110 group-hover:opacity-[0.12]', toneText[tone])}
      />

      <div className="relative flex items-start justify-between gap-3">
        <div className={cn('grid size-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br text-white shadow-lg transition-transform duration-300 group-hover:rotate-[-6deg] group-hover:scale-105', gradients[tone])}>
          <Icon className="size-5" />
        </div>
        {badge && (
          <Pill tone={badge.tone ?? 'muted'} className="shrink-0">
            {badge.pulse ? (
              <span className="relative flex size-1.5">
                <span className="absolute inset-0 animate-ping-slow rounded-full bg-current" />
                <span className="relative size-1.5 rounded-full bg-current" />
              </span>
            ) : (
              BadgeIcon && <BadgeIcon className="size-3" />
            )}
            {badge.text}
          </Pill>
        )}
      </div>

      <div className="relative mt-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-0.5 text-3xl font-semibold tracking-tight">
          <AnimatedNumber value={value} format={format} />
        </p>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </div>

      {progress && (
        <div className="relative mt-3">
          <div className="h-1.5 overflow-hidden rounded-full bg-foreground/[0.07]">
            <motion.div
              className={cn('h-full rounded-full bg-gradient-to-r', gradients[tone])}
              initial={{ width: 0 }}
              animate={{ width: `${pct * 100}%` }}
              transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">{progress.label}</p>
        </div>
      )}

      {meta && meta.length > 0 && (
        <dl className="relative mt-auto grid grid-cols-2 gap-2 border-t border-foreground/[0.06] pt-3 [&:not(:first-child)]:mt-4">
          {meta.map(({ icon: MetaIcon, label: l, value: v }) => (
            <div key={l} className="flex min-w-0 items-center gap-2">
              <span className={cn('grid size-7 shrink-0 place-items-center rounded-lg bg-foreground/[0.05] ring-1 ring-foreground/[0.06]', toneText[tone])}>
                <MetaIcon className="size-3.5" />
              </span>
              <div className="min-w-0">
                <dt className="truncate text-[11px] text-muted-foreground">{l}</dt>
                <dd className="truncate text-sm font-medium tabular-nums">{v}</dd>
              </div>
            </div>
          ))}
        </dl>
      )}
      {children}
    </motion.div>
  )
}

/** Animated RFID card graphic used in the sidebar and the empty/new-card states. */
export function TapCardGraphic({ className, pulse = true }: { className?: string; pulse?: boolean }) {
  return (
    <div className={cn('relative', className)}>
      {pulse &&
        [0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="absolute inset-0 rounded-2xl border border-brand-1/40"
            initial={{ scale: 1, opacity: 0.6 }}
            animate={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.8, ease: 'easeOut' }}
          />
        ))}
      <motion.div
        animate={{ rotateY: [0, 12, 0, -12, 0], y: [0, -3, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        className="relative aspect-[1.586] w-full overflow-hidden rounded-2xl bg-gradient-to-br from-brand-1 via-brand-2 to-brand-3 p-3 shadow-2xl shadow-brand-2/40"
        style={{ transformPerspective: 600 }}
      >
        <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent animate-shimmer" />
        <div className="h-4 w-6 rounded bg-gradient-to-br from-amber-200 to-amber-500" />
        <svg viewBox="0 0 24 24" className="absolute right-3 top-3 size-5 fill-none stroke-white/80" strokeWidth={2} strokeLinecap="round">
          <path d="M8.5 16.5a5 5 0 0 0 0-9M12 19a8.5 8.5 0 0 0 0-14M15.5 21.5a12 12 0 0 0 0-19" />
        </svg>
        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
          <div className="space-y-1">
            <div className="h-1.5 w-14 rounded bg-white/50" />
            <div className="h-1.5 w-9 rounded bg-white/30" />
          </div>
          <span className="text-[10px] font-semibold tracking-widest text-white/80">HYDRA</span>
        </div>
      </motion.div>
    </div>
  )
}
