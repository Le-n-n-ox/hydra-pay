import { useEffect, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion, useInView, useScroll, useSpring, useTransform } from 'motion/react'
import { ArrowRight, Check, ChevronDown, Code2, LayoutDashboard, Menu, Minus, Play, ShieldCheck, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { AnimatedNumber, Background } from '@/components/shared'
import { ModeToggle, ThemePicker } from '@/components/ThemeSwitcher'
import { DemoSim } from '@/landing/DemoSim'
import { HeroGraphic } from '@/landing/HeroGraphic'
import * as C from '@/landing/content'
import { cn } from '@/lib/utils'

const REPO = 'https://github.com/Le-n-n-ox/hydra-pay'
const NAV = [
  ['how', 'How it works'],
  ['demo', 'Try it'],
  ['features', 'Features'],
  ['compare', 'Compare'],
] as const

/* ---------- small building blocks ---------- */

function Section({ id, eyebrow, title, intro, children, className }: { id?: string; eyebrow: string; title: ReactNode; intro?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section id={id} className={cn('relative mx-auto max-w-6xl scroll-mt-24 px-5 py-14 sm:py-20', className)}>
      <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-80px' }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }} className="mx-auto mb-10 max-w-2xl text-center">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-brand-text">{eyebrow}</p>
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h2>
        {intro && <p className="mt-4 text-lg text-muted-foreground">{intro}</p>}
      </motion.div>
      {children}
    </section>
  )
}

function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ delay, type: 'spring', stiffness: 200, damping: 24 }} className={className}>
      {children}
    </motion.div>
  )
}

/** Number that counts up the first time it scrolls into view. */
function CountOnView({ to, suffix = '' }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const seen = useInView(ref, { once: true, margin: '-40px' })
  return <span ref={ref}><AnimatedNumber value={seen ? to : 0} format={(n) => Math.round(n) + suffix} /></span>
}

function Logo() {
  return (
    <a href="#top" className="flex items-center gap-2.5">
      <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 shadow-lg shadow-brand-1/30">
        <svg viewBox="0 0 24 24" className="size-5 fill-none stroke-white" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="5" width="20" height="14" rx="3" /><path d="M2 10h20M6 15h4" /></svg>
      </span>
      <span className="text-gradient text-lg font-bold tracking-tight">Hydra Pay</span>
    </a>
  )
}

/* ---------- nav ---------- */

function NavBar() {
  const { scrollYProgress, scrollY } = useScroll()
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 30 })
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  useEffect(() => scrollY.on('change', (y) => setScrolled(y > 20)), [scrollY])

  return (
    <header className={cn('fixed inset-x-0 top-0 z-40 transition-all duration-300', scrolled ? 'border-b border-foreground/[0.06] bg-background/70 backdrop-blur-xl' : 'bg-transparent')}>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
        <Logo />
        <nav className="hidden items-center gap-1 md:flex" aria-label="Sections">
          {NAV.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-foreground/[0.05] hover:text-foreground">{label}</a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ModeToggle />
          <ThemePicker />
          <Button className="hidden sm:inline-flex" nativeButton={false} render={<a href="/dashboard" />}><LayoutDashboard /> Open dashboard</Button>
          <Button variant="outline" size="icon" className="md:hidden" aria-label="Menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
            {open ? <X /> : <Menu />}
          </Button>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.nav initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-foreground/[0.06] bg-background/95 backdrop-blur-xl md:hidden" aria-label="Sections">
            <div className="grid gap-1 p-3">
              {NAV.map(([id, label]) => (
                <a key={id} href={`#${id}`} onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-sm hover:bg-foreground/[0.05]">{label}</a>
              ))}
              <a href="/dashboard" className="rounded-lg px-3 py-2 text-sm font-medium text-brand-text">Open dashboard →</a>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
      <motion.div style={{ scaleX: progress }} className="absolute bottom-0 left-0 h-0.5 w-full origin-left bg-gradient-to-r from-brand-1 to-brand-2" />
    </header>
  )
}

/* ---------- sections ---------- */

function Hero() {
  const words = ['Tap.', 'Pay.', 'Done.']
  return (
    <section id="top" className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 pb-16 pt-32 lg:grid-cols-[1.05fr_1fr] lg:pt-36">
      <div>
        <motion.span initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium">
          <span className="relative flex size-2"><span className="absolute inset-0 animate-ping-slow rounded-full bg-emerald-400" /><span className="relative size-2 rounded-full bg-emerald-400" /></span>
          Working prototype · DTMES 2026
        </motion.span>
        <h1 className="mt-6 text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
          {words.map((w, i) => (
            <motion.span key={w} initial={{ opacity: 0, y: 30, filter: 'blur(8px)' }} animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} transition={{ delay: 0.15 + i * 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className={cn('mr-3 inline-block', i === 2 && 'bg-gradient-to-r from-brand-1 to-brand-2 bg-clip-text text-transparent')}>
              {w}
            </motion.span>
          ))}
        </h1>
        <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="mt-6 max-w-xl text-lg text-muted-foreground sm:text-xl">
          Hydra Pay is a low-cost <b className="text-foreground">ESP32 + RFID</b> tap-card system that takes <b className="text-foreground">M-Pesa</b> payments, confirms them with Safaricom and records every sale, for businesses that serve many customers fast: canteens, market traders and matatus.
        </motion.p>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.75 }} className="mt-8 flex flex-wrap gap-3">
          <Button className="h-11 px-5 text-base" nativeButton={false} render={<a href="#demo" />}><Play /> Try the demo</Button>
          <Button variant="outline" className="h-11 px-5 text-base" nativeButton={false} render={<a href="#how" />}>How it works <ArrowRight /></Button>
        </motion.div>
        <motion.ul initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }} className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground">
          {['Verified by Safaricom', 'Receipts on WhatsApp & SMS', 'USSD for any phone'].map((t) => (
            <li key={t} className="flex items-center gap-1.5"><Check className="size-4 text-good" />{t}</li>
          ))}
        </motion.ul>
      </div>
      <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}>
        <HeroGraphic />
      </motion.div>
      <motion.a href="#problem" aria-label="Scroll down" animate={{ y: [0, 8, 0] }} transition={{ duration: 2, repeat: Infinity }} className="absolute bottom-2 left-1/2 hidden -translate-x-1/2 text-muted-foreground lg:block">
        <ChevronDown />
      </motion.a>
    </section>
  )
}

function TechStrip() {
  const items = ['ESP32 + RC522', 'M-Pesa Daraja', 'WhatsApp', 'Gemini AI', 'ElevenLabs voice', 'SMS + USSD', 'Flask + SQLite', 'React dashboard']
  return (
    <div className="relative overflow-hidden border-y border-foreground/[0.06] py-5 [mask-image:linear-gradient(90deg,transparent,black_12%,black_88%,transparent)]">
      <motion.div className="flex w-max gap-10" animate={{ x: ['0%', '-50%'] }} transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}>
        {[...items, ...items].map((t, i) => (
          <span key={i} className="flex items-center gap-2 whitespace-nowrap text-sm font-medium text-muted-foreground">
            <span className="size-1.5 rounded-full bg-gradient-to-r from-brand-1 to-brand-2" />{t}
          </span>
        ))}
      </motion.div>
    </div>
  )
}

function Problem() {
  return (
    <Section id="problem" eyebrow="The problem" title="Busy small businesses lose time and money at the till" intro="Owners need an affordable way to accept, verify and record payments without slowing down.">
      <div className="grid gap-5 md:grid-cols-3">
        {C.problems.map((p, i) => (
          <Reveal key={p.title} delay={i * 0.08}>
            <motion.div whileHover={{ y: -6 }} className="glass h-full rounded-3xl p-6">
              <div className="mb-4 grid size-12 place-items-center rounded-2xl bg-rose-500/15 text-bad ring-1 ring-rose-500/25"><p.icon className="size-6" /></div>
              <h3 className="text-lg font-semibold">{p.title}</h3>
              <p className="mt-2 text-muted-foreground">{p.body}</p>
            </motion.div>
          </Reveal>
        ))}
      </div>
      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        {C.stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.1}>
            <div className="glass flex items-center gap-5 rounded-3xl p-6">
              <p className="bg-gradient-to-br from-brand-1 to-brand-2 bg-clip-text text-5xl font-bold tabular-nums text-transparent sm:text-6xl"><CountOnView to={s.value} suffix={s.suffix} /></p>
              <p className="text-muted-foreground">{s.label}</p>
            </div>
          </Reveal>
        ))}
      </div>
      <p className="mt-4 text-center text-xs text-muted-foreground">{C.statsSource}</p>
    </Section>
  )
}

function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 75%', 'end 55%'] })
  const line = useSpring(scrollYProgress, { stiffness: 100, damping: 30 })
  const [mode, setMode] = useState<'prompt' | 'wallet'>('prompt')
  const M = C.modes[mode]

  return (
    <Section id="how" eyebrow="How it works" title="One tap: pay, verify and record in one flow" intro="The customer only taps and enters their M-Pesa PIN. Everything else happens automatically.">
      <div ref={ref} className="relative mx-auto max-w-3xl">
        <div className="absolute bottom-6 left-6 top-6 w-0.5 bg-foreground/10 sm:left-1/2 sm:-translate-x-1/2" />
        <motion.div style={{ scaleY: line }} className="absolute bottom-6 left-6 top-6 w-0.5 origin-top bg-gradient-to-b from-brand-1 to-brand-2 sm:left-1/2 sm:-translate-x-1/2" />
        <ol className="grid gap-10">
          {C.steps.map((s, i) => (
            <li key={s.title} className={cn('relative grid items-center gap-4 pl-16 sm:grid-cols-2 sm:gap-16 sm:pl-0', i % 2 && 'sm:[&>div:first-of-type]:order-2')}>
              <motion.span initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true, margin: '-100px' }} transition={{ type: 'spring', stiffness: 300, damping: 18 }}
                className="absolute left-6 top-1/2 z-10 grid size-12 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-gradient-to-br from-brand-1 to-brand-2 text-lg font-bold text-white shadow-lg shadow-brand-1/40 ring-4 ring-background sm:left-1/2">
                {i + 1}
              </motion.span>
              <Reveal className={cn(i % 2 ? 'sm:pl-10' : 'sm:pr-10 sm:text-right')}>
                <h3 className="text-2xl font-semibold">{s.title}</h3>
                <p className="mt-2 text-muted-foreground">{s.body}</p>
              </Reveal>
              <Reveal delay={0.1} className={cn(i % 2 ? 'sm:pr-10' : 'sm:pl-10')}>
                <div className="glass rounded-2xl p-4 text-sm text-muted-foreground">{s.detail}</div>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>

      <Reveal className="mx-auto mt-20 max-w-3xl">
        <div className="glass rounded-3xl p-6 sm:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <h3 className="text-xl font-semibold">Two ways to charge</h3>
            <div className="flex rounded-xl bg-muted p-1">
              {(Object.keys(C.modes) as (keyof typeof C.modes)[]).map((m) => {
                const Icon = C.modes[m].icon
                return (
                  <button key={m} onClick={() => setMode(m)} className={cn('relative rounded-lg px-4 py-1.5 text-sm font-medium', mode === m ? 'text-foreground' : 'text-muted-foreground')}>
                    {mode === m && <motion.span layoutId="mode-tab" className="absolute inset-0 rounded-lg bg-background shadow-sm ring-1 ring-foreground/10" transition={{ type: 'spring', stiffness: 400, damping: 30 }} />}
                    <span className="relative flex items-center gap-1.5"><Icon className="size-4" />{C.modes[m].label}</span>
                  </button>
                )
              })}
            </div>
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={mode} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
              <p className="text-lg">{M.summary}</p>
              <ul className="mt-4 grid gap-2 sm:grid-cols-3">
                {M.bullets.map((b) => (
                  <li key={b} className="flex gap-2 rounded-xl bg-foreground/[0.04] p-3 text-sm ring-1 ring-foreground/[0.06]"><Check className="mt-0.5 size-4 shrink-0 text-good" />{b}</li>
                ))}
              </ul>
            </motion.div>
          </AnimatePresence>
        </div>
      </Reveal>
    </Section>
  )
}

function Demo() {
  return (
    <Section id="demo" eyebrow="Try it" title="See a payment land on the dashboard" intro="This is a simulation of the real dashboard: tap a card, watch the M-Pesa prompt, and see the record appear the moment Safaricom confirms.">
      <Reveal><DemoSim /></Reveal>
    </Section>
  )
}

function Features() {
  return (
    <Section id="features" eyebrow="Everything it does" title="Built for the till, the queue and the end of the day">
      <div className="grid auto-rows-fr grid-flow-dense gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {C.features.map((f, i) => (
          <Reveal key={f.title} delay={(i % 4) * 0.05} className={cn(f.wide && 'lg:col-span-2')}>
            <motion.div whileHover={{ y: -5 }} className="glass group relative h-full overflow-hidden rounded-3xl p-5">
              <div className="absolute -right-12 -top-12 size-36 rounded-full bg-gradient-to-br from-brand-1 to-brand-2 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-25" />
              <div className="mb-4 grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-1 to-brand-2 text-white shadow-lg shadow-brand-1/25 transition-transform duration-300 group-hover:rotate-[-6deg] group-hover:scale-110">
                <f.icon className="size-5" />
              </div>
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.body}</p>
            </motion.div>
          </Reveal>
        ))}
      </div>
    </Section>
  )
}

function MarkIcon({ m }: { m: C.Mark }) {
  if (m === 'yes') return <span className="mx-auto grid size-7 place-items-center rounded-full bg-emerald-500/15 text-good ring-1 ring-emerald-500/30" aria-label="Yes"><Check className="size-4" strokeWidth={3} /></span>
  if (m === 'partial') return <span className="mx-auto grid size-7 place-items-center rounded-full bg-amber-500/15 text-warn ring-1 ring-amber-500/30" aria-label="Partly"><Minus className="size-4" strokeWidth={3} /></span>
  return <span className="mx-auto grid size-7 place-items-center rounded-full bg-rose-500/10 text-bad ring-1 ring-rose-500/20" aria-label="No"><X className="size-4" strokeWidth={3} /></span>
}

function Compare() {
  return (
    <Section id="compare" eyebrow="How it's different" title="Less friction at the till, clearer records after it" intro="Hydra Pay doesn't replace M-Pesa. It sits on top of the habits people already have and fixes the slow, unverified and unrecorded parts.">
      <Reveal>
        <div className="glass overflow-x-auto rounded-3xl">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-foreground/[0.06]">
                <th className="p-4 text-left font-medium text-muted-foreground" />
                {C.compareColumns.map((c, i) => (
                  <th key={c} className={cn('p-4 text-center font-semibold', i === 0 && 'relative')}>
                    {i === 0 && <span className="absolute inset-x-1 inset-y-1 -z-10 rounded-xl bg-gradient-to-b from-brand-1/20 to-brand-2/5" />}
                    <span className={cn(i === 0 && 'text-brand-text')}>{c}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {C.compareRows.map((r, ri) => (
                <motion.tr key={r.label} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: ri * 0.05 }} className="border-b border-foreground/[0.05] last:border-0">
                  <td className="p-4">
                    <p className="font-medium">{r.label}</p>
                    {r.note && <p className="text-xs text-muted-foreground">{r.note}</p>}
                  </td>
                  {r.marks.map((m, i) => (
                    <td key={i} className={cn('p-4 text-center', i === 0 && 'bg-brand-1/[0.06]')}>
                      <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.1 + ri * 0.05 + i * 0.03, type: 'spring', stiffness: 400, damping: 18 }}>
                        <MarkIcon m={m} />
                      </motion.div>
                    </td>
                  ))}
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-center text-xs text-muted-foreground">{C.compareFootnote}</p>
      </Reveal>

    </Section>
  )
}

function Trust() {
  return (
    <Section eyebrow="Safety & proof" title="Designed for real money">
      <Reveal>
        <div className="glass relative grid gap-8 overflow-hidden rounded-3xl p-6 sm:p-8 lg:grid-cols-[1.1fr_1fr]">
          <div className="absolute inset-0 -z-10 bg-gradient-to-br from-brand-1/10 to-brand-2/10" />
          <ul className="grid gap-4">
            {C.risks.map(([risk, answer]) => (
              <li key={risk} className="flex gap-3">
                <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-emerald-500/15 text-good ring-1 ring-emerald-500/25"><ShieldCheck className="size-4" /></span>
                <div><p className="font-semibold">{risk}</p><p className="text-sm text-muted-foreground">{answer}</p></div>
              </li>
            ))}
          </ul>
          <div className="grid content-center gap-5 sm:grid-cols-3 lg:border-l lg:border-foreground/[0.08] lg:pl-8">
            {C.proof.map((p) => (
              <div key={p.label} className="text-center">
                <p className="bg-gradient-to-br from-brand-1 to-brand-2 bg-clip-text text-4xl font-bold tabular-nums text-transparent"><CountOnView to={p.value} /></p>
                <p className="mt-1 text-xs text-muted-foreground">{p.label}</p>
              </div>
            ))}
            <p className="text-center text-xs text-muted-foreground sm:col-span-3">{C.proofNote}</p>
          </div>
        </div>
      </Reveal>
    </Section>
  )
}

function Markets() {
  return (
    <Section eyebrow="Who it's for" title="Businesses where every second counts">
      <div className="grid gap-5 md:grid-cols-3">
        {C.markets.map((m, i) => (
          <Reveal key={m.title} delay={i * 0.08}>
            <motion.div whileHover={{ y: -6 }} className="glass h-full rounded-3xl p-6">
              <div className="mb-4 flex items-center justify-between">
                <span className="grid size-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-1 to-brand-2 text-white shadow-lg shadow-brand-1/25"><m.icon className="size-6" /></span>
                <span className={cn('rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1', m.tag === 'Next' ? 'bg-foreground/5 text-muted-foreground ring-foreground/10' : 'bg-emerald-500/15 text-good ring-emerald-500/30')}>{m.tag}</span>
              </div>
              <h3 className="text-lg font-semibold">{m.title}</h3>
              <p className="mt-2 text-muted-foreground">{m.body}</p>
              <p className="mt-3 text-sm"><b>Need:</b> <span className="text-muted-foreground">{m.need}</span></p>
            </motion.div>
          </Reveal>
        ))}
      </div>
    </Section>
  )
}

function FinalCta() {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const rotate = useTransform(scrollYProgress, [0, 1], [-8, 8])
  return (
    <section className="mx-auto max-w-6xl px-5 pb-24">
      <div ref={ref} className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-brand-1 via-brand-2 to-brand-3 p-10 text-center text-white shadow-2xl shadow-brand-2/30 sm:p-16">
        <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/15 to-transparent animate-shimmer" />
        <motion.div style={{ rotate }} className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full border-[28px] border-white/10" />
        <motion.div style={{ rotate }} className="pointer-events-none absolute -bottom-20 -left-10 size-72 rounded-full border-[32px] border-white/10" />
        <h2 className="relative text-4xl font-bold tracking-tight sm:text-5xl">Tap. Pay. Done.</h2>
        <p className="relative mx-auto mt-4 max-w-xl text-lg text-white/85">Fast payments, safer transactions, clearer records, on hardware that costs less than a phone.</p>
        <div className="relative mt-8 flex flex-wrap justify-center gap-3">
          <Button className="h-11 bg-white bg-none px-5 text-base text-slate-900 shadow-xl hover:bg-white/90" nativeButton={false} render={<a href="/dashboard" />}><LayoutDashboard /> Open the dashboard</Button>
          <Button variant="outline" className="h-11 border-white/40 bg-white/10 px-5 text-base text-white hover:bg-white/20 hover:text-white" nativeButton={false} render={<a href={REPO} target="_blank" rel="noreferrer" />}><Code2 /> View the code</Button>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-foreground/[0.06]">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-8 text-sm text-muted-foreground">
        <Logo />
        <p>Team HYDRA-PAY · Technical University of Kenya · DTMES 2026</p>
        <a href={REPO} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:text-foreground"><Code2 className="size-4" /> GitHub</a>
      </div>
    </footer>
  )
}

export default function Landing() {
  return (
    <>
      <Background />
      <NavBar />
      <main className="overflow-x-clip">
        <Hero />
        <TechStrip />
        <Problem />
        <HowItWorks />
        <Demo />
        <Features />
        <Compare />
        <Trust />
        <Markets />
        <FinalCta />
      </main>
      <Footer />
    </>
  )
}
