import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Ban, Banknote, CreditCard, MoreHorizontal, Pencil, Phone, Plus, Search, ShieldCheck } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { EmptyState, PersonAvatar, Pill, fadeUp, stagger } from '@/components/shared'
import { useAdmin } from '@/hooks/useAdmin'
import type { Card, CardSummary } from '@/lib/api'
import { hue } from '@/lib/format'

export function Cards({ cards, perCard, mode, onAdd, onEdit, onTopup, reload }: {
  cards: Card[]
  perCard: CardSummary[]
  mode: 'prompt' | 'wallet'
  onAdd: () => void
  onEdit: (c: Card) => void
  onTopup: (c: Card) => void
  reload: () => void
}) {
  const post = useAdmin()
  const [q, setQ] = useState('')
  const stats = useMemo(() => new Map(perCard.map((c) => [c.uid, c])), [perCard])
  const rows = cards.filter((c) => !q || [c.name, c.phone, c.uid].some((v) => (v || '').toLowerCase().includes(q.toLowerCase())))

  const toggleBlock = async (c: Card) => {
    if (await post('/api/cards/block', { uid: c.uid, blocked: !c.blocked })) reload()
  }

  const addForCard = async (c: Card) => {
    // Uses the card's saved M-Pesa number and its configured per-tap amount.
    if (await post('/api/topup/mpesa', { uid: c.uid, amount: c.price })) reload()
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="grid gap-5">
      <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-0 flex-1 basis-56">
          <Search className="pointer-events-none absolute left-3 top-1/2 z-10 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by name, phone or UID" className="glass h-10 pl-9" />
        </div>
        <Button variant="success" onClick={onAdd} className="h-10">
          <Plus /> Add card
        </Button>
      </motion.div>

      <motion.p variants={fadeUp} className="text-sm text-muted-foreground">
        Card owners can change their own number on WhatsApp (send <b className="text-foreground">3</b>). Lost card? Tap the new one on the reader and choose <b className="text-foreground">Move to this card</b>.
      </motion.p>

      {rows.length ? (
        <motion.div variants={stagger} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          <AnimatePresence>
            {rows.map((c) => {
              const st = stats.get(c.uid)
              const h = hue(c.name)
              return (
                <motion.article
                  key={c.uid}
                  layout
                  variants={fadeUp}
                  exit={{ opacity: 0, scale: 0.9 }}
                  whileHover={{ y: -4 }}
                  className="glass group relative overflow-hidden rounded-2xl"
                >
                  <div className="relative h-20 overflow-hidden" style={{ background: `linear-gradient(135deg, hsl(${h} 65% 45% / .9), hsl(${(h + 60) % 360} 60% 35% / .8))` }}>
                    <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/15 to-transparent group-hover:animate-shimmer" />
                    <svg viewBox="0 0 24 24" className="absolute right-4 top-4 size-6 fill-none stroke-white/60" strokeWidth={2} strokeLinecap="round">
                      <path d="M8.5 16.5a5 5 0 0 0 0-9M12 19a8.5 8.5 0 0 0 0-14M15.5 21.5a12 12 0 0 0 0-19" />
                    </svg>
                    <span className="absolute left-4 top-4 font-mono text-xs tracking-widest text-white/75">{c.uid}</span>
                  </div>
                  <div className="p-4 pt-0">
                    <div className="relative -mt-6 flex items-end justify-between">
                      <PersonAvatar name={c.name} className="size-12 text-sm ring-4 ring-background" />
                      <div className="flex items-center gap-1.5">
                        {c.blocked ? <Pill tone="red"><Ban className="size-3" />Blocked</Pill> : c.status === 'IN' ? <Pill tone="green">IN</Pill> : <Pill>OUT</Pill>}
                        <Button
                          size="icon-sm"
                          variant="ghost"
                          className="text-muted-foreground/70 hover:text-foreground"
                          aria-label={`Add credit for ${c.name}`}
                          title={`Add KSh ${c.price}`}
                          onClick={() => void addForCard(c)}
                          disabled={!c.phone || c.price <= 0 || !!c.blocked}
                        >
                          <Plus />
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger render={<Button size="icon-sm" variant="ghost" aria-label={`Actions for ${c.name}`} />}>
                            <MoreHorizontal />
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-44">
                            <DropdownMenuItem onClick={() => onEdit(c)}><Pencil /> Edit</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => onTopup(c)}><Banknote /> Top up</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem variant={c.blocked ? 'default' : 'destructive'} onClick={() => toggleBlock(c)}>
                              {c.blocked ? <><ShieldCheck /> Unblock</> : <><Ban /> Block card</>}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                    <h3 className="mt-3 truncate font-semibold">{c.name}</h3>
                    <p className="flex items-center gap-1.5 text-sm text-muted-foreground"><Phone className="size-3.5" />{c.phone || 'No phone'}</p>
                    <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
                      {[
                        ['Per tap', `KSh ${c.price}`],
                        [mode === 'wallet' ? 'Balance' : 'Spent today', mode === 'wallet' ? `KSh ${c.balance}` : `KSh ${st?.spent ?? 0}`],
                        ['Taps today', String(st?.taps ?? 0)],
                      ].map(([k, v]) => (
                        <div key={k} className="rounded-xl bg-foreground/[0.04] px-2 py-2 ring-1 ring-foreground/[0.06]">
                          <dt className="text-[11px] text-muted-foreground">{k}</dt>
                          <dd className="text-sm font-semibold tabular-nums">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </motion.article>
              )
            })}
          </AnimatePresence>
        </motion.div>
      ) : (
        <EmptyState icon={CreditCard} title={cards.length ? 'No cards match' : 'No cards yet'} hint={cards.length ? 'Try a different search.' : 'Tap a card on the reader, then register it.'} />
      )}
    </motion.div>
  )
}
