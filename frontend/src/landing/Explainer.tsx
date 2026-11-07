// "How the whole system works" sections: one payment step by step, the parts, features,
// what happens when things go wrong, getting started and FAQ.
import { Fragment, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowDown, ArrowRight, ChevronDown, Store, Users } from 'lucide-react'

import { Reveal, Section } from '@/landing/blocks'
import * as D from '@/landing/details'
import { cn } from '@/lib/utils'

const whereStyle: Record<(typeof D.journey)[number]['where'], string> = {
  Counter: 'bg-brand-1/15 text-brand-text ring-brand-1/30',
  'Hydra Pay': 'bg-brand-2/15 text-brand-text ring-brand-2/30',
  "Customer's phone": 'bg-amber-500/15 text-warn ring-amber-500/30',
  Safaricom: 'bg-emerald-500/15 text-good ring-emerald-500/30',
}

export function Journey() {
  return (
    <Section id="journey" eyebrow="Behind the scenes" title="One payment, step by step" intro="Everything that happens between the tap and the receipt, in a few seconds.">
      <div className="mb-8 flex flex-wrap justify-center gap-2">
        {(Object.keys(whereStyle) as (keyof typeof whereStyle)[]).map((w) => (
          <span key={w} className={cn('rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset', whereStyle[w])}>{w}</span>
        ))}
      </div>
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {D.journey.map((s, i) => (
          <Reveal key={s.title} delay={(i % 4) * 0.07}>
            <motion.li whileHover={{ y: -4 }} className="glass relative flex h-full flex-col rounded-2xl p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 text-white shadow-lg shadow-brand-1/25">
                  <s.icon className="size-5" />
                </span>
                <span className="text-3xl font-bold tabular-nums text-foreground/10">{String(i + 1).padStart(2, '0')}</span>
              </div>
              <span className={cn('mb-2 w-fit rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ring-inset', whereStyle[s.where])}>{s.where}</span>
              <h3 className="font-semibold">{s.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{s.body}</p>
            </motion.li>
          </Reveal>
        ))}
      </ol>
    </Section>
  )
}

function PartCard({ part, highlight }: { part: (typeof D.parts)[number]; highlight?: boolean }) {
  return (
    <motion.div whileHover={{ y: -4 }} className={cn('glass h-full rounded-2xl p-5', highlight && 'ring-2 ring-brand-1/50')}>
      <span className={cn('mb-3 grid size-11 place-items-center rounded-xl text-white shadow-lg', highlight ? 'bg-gradient-to-br from-brand-1 to-brand-2 shadow-brand-1/30' : 'bg-foreground/10 text-foreground shadow-none')}>
        <part.icon className="size-5" />
      </span>
      <h3 className="font-semibold">{part.title}</h3>
      <p className="mt-1.5 text-sm text-muted-foreground">{part.body}</p>
    </motion.div>
  )
}

export function SystemParts() {
  const chain = D.parts.slice(0, 4)
  const outputs = D.parts.slice(4)
  return (
    <Section id="system" eyebrow="The system" title="Six parts working together" intro="From the card in a customer's hand to the money in your till.">
      <div className="grid items-stretch gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
        {chain.map((p, i) => (
          <Fragment key={p.title}>
            <Reveal delay={i * 0.08}><PartCard part={p} highlight={i === 2} /></Reveal>
            {i < chain.length - 1 && (
              <div className="grid place-items-center text-muted-foreground" aria-hidden>
                <ArrowRight className="hidden size-5 lg:block" />
                <ArrowDown className="size-5 lg:hidden" />
              </div>
            )}
          </Fragment>
        ))}
      </div>
      <Reveal className="mx-auto mt-6 max-w-3xl">
        <p className="mb-3 text-center text-sm text-muted-foreground">Hydra Pay also keeps you and your customers up to date:</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {outputs.map((p) => <PartCard key={p.title} part={p} />)}
        </div>
      </Reveal>
    </Section>
  )
}

export function Features() {
  const [tab, setTab] = useState<'customers' | 'owners'>('owners')
  const tabs = [
    { id: 'owners' as const, label: 'For you, the owner', Icon: Store, items: D.forOwners },
    { id: 'customers' as const, label: 'For your customers', Icon: Users, items: D.forCustomers },
  ]
  const items = tabs.find((t) => t.id === tab)!.items
  return (
    <Section id="features" eyebrow="Features" title="Everything it does">
      <div className="mb-8 flex justify-center">
        <div className="flex rounded-xl bg-muted p-1">
          {tabs.map(({ id, label, Icon }) => (
            <button key={id} onClick={() => setTab(id)} className={cn('relative rounded-lg px-4 py-2 text-sm font-medium', tab === id ? 'text-foreground' : 'text-muted-foreground')}>
              {tab === id && <motion.span layoutId="feature-tab" className="absolute inset-0 rounded-lg bg-background shadow-sm ring-1 ring-foreground/10" transition={{ type: 'spring', stiffness: 400, damping: 30 }} />}
              <span className="relative flex items-center gap-2"><Icon className="size-4" />{label}</span>
            </button>
          ))}
        </div>
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={tab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.25 }} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((f) => (
            <motion.div key={f.title} whileHover={{ y: -4 }} className="glass group flex gap-4 rounded-2xl p-5">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-1/15 text-brand-text ring-1 ring-brand-1/25 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110">
                <f.icon className="size-5" />
              </span>
              <div>
                <h3 className="font-semibold">{f.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{f.body}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>
    </Section>
  )
}

export function WhatIf() {
  return (
    <Section id="what-if" eyebrow="What if…" title="When things don't go to plan" intro="Hydra Pay is built for real counters, slow networks and lost cards.">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {D.whatIf.map((w, i) => (
          <Reveal key={w.title} delay={(i % 4) * 0.06}>
            <div className="glass h-full rounded-2xl p-5">
              <span className="mb-3 grid size-9 place-items-center rounded-lg bg-foreground/[0.06] text-muted-foreground ring-1 ring-foreground/10">
                <w.icon className="size-4.5" />
              </span>
              <h3 className="text-sm font-semibold">{w.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{w.body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  )
}

export function GetStarted() {
  return (
    <Section id="start" eyebrow="Getting started" title="Up and running in five steps">
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {D.getStarted.map((s, i) => (
          <Reveal key={s.title} delay={i * 0.07}>
            <li className="glass relative h-full rounded-2xl p-5">
              <span className="absolute right-4 top-4 grid size-7 place-items-center rounded-full bg-gradient-to-br from-brand-1 to-brand-2 text-xs font-bold text-white">{i + 1}</span>
              <s.icon className="mb-3 size-6 text-brand-text" />
              <h3 className="font-semibold">{s.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{s.body}</p>
            </li>
          </Reveal>
        ))}
      </ol>
    </Section>
  )
}

export function Faq() {
  const [open, setOpen] = useState<number | null>(0)
  return (
    <Section id="faq" eyebrow="Questions" title="Frequently asked">
      <Reveal className="mx-auto max-w-3xl">
        <div className="glass divide-y divide-foreground/[0.06] rounded-3xl">
          {D.faq.map(([q, a], i) => (
            <div key={q}>
              <button onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i} className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left font-medium">
                {q}
                <ChevronDown className={cn('size-4 shrink-0 text-muted-foreground transition-transform duration-300', open === i && 'rotate-180')} />
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }} className="overflow-hidden">
                    <p className="px-6 pb-5 text-muted-foreground">{a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </Reveal>
    </Section>
  )
}
