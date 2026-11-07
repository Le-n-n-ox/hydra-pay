import type { ReactNode } from 'react'
import { motion } from 'motion/react'

import { cn } from '@/lib/utils'

export function Section({ id, eyebrow, title, intro, children, className }: { id?: string; eyebrow: string; title: ReactNode; intro?: ReactNode; children: ReactNode; className?: string }) {
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

export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ delay, type: 'spring', stiffness: 200, damping: 24 }} className={className}>
      {children}
    </motion.div>
  )
}
