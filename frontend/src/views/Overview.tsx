import { AnimatePresence, motion } from 'motion/react'
import { Activity, BadgeCheck, Banknote, BarChart3, CalendarDays, CircleCheck, CircleX, Coins, DoorOpen, IdCard, PhoneOff, PieChart, Radio, ScanLine, ShieldCheck, Smartphone, TriangleAlert, Users, Wallet, WalletMinimal } from 'lucide-react'

import { ActivityChart, PaymentMixChart, TopSpendersChart } from '@/components/charts'
import { EmptyState, Panel, PaymentBadge, PersonAvatar, Pill, StatCard, stagger } from '@/components/shared'
import type { DashboardData } from '@/lib/api'
import { hhmm, ksh, shortTime, today } from '@/lib/format'

type FeedItem = { key: string; uid: string; dir?: string; time: string; name: string; kind: 'pay' | 'tap'; text: string; status?: string; tone?: 'green' | 'red' | 'muted' | 'amber' }

function buildFeed(d: DashboardData): FeedItem[] {
  const names = new Map(d.cards.map((c) => [c.uid, c.name]))
  const pays: FeedItem[] = d.payments.slice(0, 12).map((p) => ({
    key: 'p' + p.id,
    uid: p.uid,
    time: p.time,
    name: p.name || names.get(p.uid) || p.phone,
    kind: 'pay',
    text: `KSh ${p.amount} · M-Pesa`,
    status: p.status,
  }))
  const taps: FeedItem[] = d.scans.slice(0, 12).map((s) => ({
    key: 's' + s.id,
    uid: s.uid,
    dir: s.direction,
    time: s.time,
    name: names.get(s.uid) || 'Unknown card',
    kind: 'tap',
    text: names.has(s.uid) ? `Tapped ${s.direction} · ${s.result}` : `Card ${s.uid} · ${s.result}`,
    tone: s.result === 'blocked' || s.result === 'low balance' ? 'red' : s.direction === 'IN' ? 'green' : 'muted',
  }))
  return [...pays, ...taps].sort((a, b) => b.time.localeCompare(a.time)).slice(0, 10)
}

export function Overview({ data: d }: { data: DashboardData }) {
  const s = d.summary
  const day = today()
  const paidTaps = s.per_card.reduce((n, c) => n + c.paid_taps, 0)
  const collected = Number(s.mpesa) + Number(s.cash || 0)
  const unpaid = Number(s.swipe_unpaid) + Number(s.denied || 0)
  const feed = buildFeed(d)
  const names = new Map(d.cards.map((c) => [c.uid, c.name]))

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="grid gap-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Wallet} tone="green" label="Collected today" value={collected} format={ksh}
          badge={{ icon: CalendarDays, text: 'Today', tone: 'green' }}
          meta={[
            { icon: Smartphone, label: 'M-Pesa', value: ksh(s.mpesa) },
            { icon: Banknote, label: 'Cash', value: ksh(s.cash || 0) },
          ]}
        />
        <StatCard
          icon={BadgeCheck} tone="blue" label="Paid taps" value={paidTaps}
          badge={{ icon: ShieldCheck, text: 'Verified', tone: 'blue' }}
          progress={{ value: s.taps ? paidTaps / s.taps : 0, label: s.taps ? `${Math.round((paidTaps / s.taps) * 100)}% of today's taps were paid` : 'No taps yet today' }}
          meta={[
            { icon: ScanLine, label: 'All taps', value: s.taps },
            { icon: Coins, label: 'From taps', value: ksh(Number(s.swipe_paid) + Number(s.tap_revenue || 0)) },
          ]}
        />
        <StatCard
          icon={CircleX} tone="red" label="Didn't pay" value={unpaid}
          badge={unpaid ? { icon: TriangleAlert, text: 'Check', tone: 'red' } : { icon: CircleCheck, text: 'All clear', tone: 'green' }}
          meta={[
            { icon: PhoneOff, label: 'Failed', value: Number(s.swipe_unpaid) || 0 },
            { icon: WalletMinimal, label: 'Low balance', value: Number(s.denied) || 0 },
          ]}
        />
        <StatCard
          icon={Users} tone="violet" label="Inside now" value={d.inside.length}
          badge={{ text: 'Live', tone: 'violet', pulse: true }}
          progress={{ value: d.cards.length ? d.inside.length / d.cards.length : 0, label: `${d.inside.length} of ${d.cards.length} card holders checked in` }}
          meta={[
            { icon: IdCard, label: 'Registered', value: d.cards.length },
            { icon: DoorOpen, label: 'Outside', value: Math.max(0, d.cards.length - d.inside.length) },
          ]}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel title="Today's activity" icon={BarChart3} className="xl:col-span-2"
          action={<div className="flex gap-3 text-xs text-muted-foreground"><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-chart-1" />Collected</span><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-chart-2" />Taps</span></div>}>
          <ActivityChart payments={d.payments} scans={d.scans} day={day} />
        </Panel>
        <Panel title="Payment outcomes" icon={PieChart}>
          <PaymentMixChart payments={d.payments} day={day} />
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel title="Live feed" icon={Radio} className="xl:col-span-2" bodyClassName="p-2"
          action={<Pill tone="green"><span className="size-1.5 animate-pulse rounded-full bg-emerald-400" />Live</Pill>}>
          {feed.length ? (
            <ul className="divide-y divide-white/[0.05]">
              <AnimatePresence initial={false}>
                {feed.map((f) => (
                  <motion.li
                    key={f.key}
                    layout
                    initial={{ opacity: 0, x: -24, backgroundColor: 'rgba(96,165,250,0.18)' }}
                    animate={{ opacity: 1, x: 0, backgroundColor: 'rgba(96,165,250,0)' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.5 }}
                    className="flex items-center gap-3 rounded-xl px-3 py-2.5"
                  >
                    <PersonAvatar name={f.name} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{f.name}</p>
                      <p className="truncate text-xs text-muted-foreground">{f.text}</p>
                    </div>
                    {/* status above the time on phones, side by side from sm up */}
                    <div className="flex min-w-0 max-w-[55%] shrink-0 flex-col items-end gap-1 sm:max-w-none sm:flex-row sm:items-center sm:gap-3">
                      {f.status ? <PaymentBadge status={f.status} className="max-w-full sm:max-w-[16rem]" /> : <Pill tone={f.tone}>{f.kind === 'tap' ? <Activity className="size-3" /> : null}{names.has(f.uid) ? f.dir : 'New'}</Pill>}
                      <span className="whitespace-nowrap text-right text-xs tabular-nums text-muted-foreground">{f.time.startsWith(day) ? hhmm(f.time) : shortTime(f.time)}</span>
                    </div>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          ) : (
            <EmptyState icon={Radio} title="Waiting for the first tap" hint="Taps and M-Pesa payments show up here the moment they happen." />
          )}
        </Panel>

        <div className="grid gap-5">
          <Panel title="Top cards today" icon={BarChart3}>
            <TopSpendersChart perCard={s.per_card} />
          </Panel>
          <Panel title="Inside now" icon={DoorOpen} action={<Pill tone="violet">{d.inside.length}</Pill>}>
            {d.inside.length ? (
              <div className="flex flex-wrap gap-2">
                <AnimatePresence>
                  {d.inside.map((c) => (
                    <motion.span key={c.uid} layout initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.6, opacity: 0 }}
                      className="flex items-center gap-2 rounded-full bg-foreground/5 py-1 pl-1 pr-3 text-sm ring-1 ring-foreground/10">
                      <PersonAvatar name={c.name} className="size-7 text-[10px]" />
                      {c.name}
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Nobody is checked in.</p>
            )}
          </Panel>
        </div>
      </div>
    </motion.div>
  )
}
