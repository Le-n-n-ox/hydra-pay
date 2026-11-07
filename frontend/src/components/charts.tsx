import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { CardSummary, Payment, Scan } from '@/lib/api'
import { byHour, ksh, payState } from '@/lib/format'
import { useThemeColors } from '@/hooks/useTheme'

/** Chart colours come from the active theme (src/themes.css), so charts follow light/dark and palette changes. */
function useColors() {
  const c = useThemeColors()
  return {
    green: c.chart1, blue: c.chart2, violet: c.brand2, brand: c.brand1,
    good: c.good, warn: c.warn, bad: c.bad, grid: c.grid, axis: c.axis, track: c.track,
  }
}

function ChartTooltip({ active, payload, label, money }: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
  money?: string[]
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-border bg-popover/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
      {label && <p className="mb-1 font-medium text-foreground">{label}</p>}
      {payload.map((p) => (
        <p key={p.name} className="flex items-center gap-2 text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: p.color }} />
          {p.name}: <span className="font-medium text-foreground">{money?.includes(p.name) ? ksh(p.value) : p.value}</span>
        </p>
      ))}
    </div>
  )
}

/** Money collected (paid M-Pesa) and card taps per hour for the day. */
export function ActivityChart({ payments, scans, day }: { payments: Payment[]; scans: Scan[]; day: string }) {
  const COLORS = useColors()
  const money = byHour(payments, day, (p) => (p.status === 'PAID' ? Number(p.amount) || 0 : 0))
  const taps = byHour(scans, day, () => 1)
  const offset = money.length - taps.length
  const data = money.map((m, i) => ({ hour: m.hour, Collected: m.value, Taps: taps[i - offset]?.value ?? 0 }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 10, right: 8, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="gCollected" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.green} stopOpacity={0.45} />
            <stop offset="100%" stopColor={COLORS.green} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gTaps" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.blue} stopOpacity={0.35} />
            <stop offset="100%" stopColor={COLORS.blue} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={COLORS.grid} vertical={false} />
        <XAxis dataKey="hour" tick={{ fill: COLORS.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis yAxisId="money" tick={{ fill: COLORS.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
        <YAxis yAxisId="taps" orientation="right" allowDecimals={false} tick={{ fill: COLORS.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
        <Tooltip content={<ChartTooltip money={['Collected']} />} cursor={{ stroke: COLORS.axis, strokeOpacity: 0.3 }} />
        <Area yAxisId="money" type="monotone" dataKey="Collected" stroke={COLORS.green} strokeWidth={2.5} fill="url(#gCollected)" animationDuration={900} />
        <Area yAxisId="taps" type="monotone" dataKey="Taps" stroke={COLORS.blue} strokeWidth={2} fill="url(#gTaps)" animationDuration={1100} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

/** Donut of today's M-Pesa prompts by outcome. */
export function PaymentMixChart({ payments, day }: { payments: Payment[]; day: string }) {
  const COLORS = useColors()
  const todays = payments.filter((p) => p.time?.startsWith(day))
  const count = (s: ReturnType<typeof payState>) => todays.filter((p) => payState(p.status) === s).length
  const data = [
    { name: 'Paid', value: count('paid'), color: COLORS.good },
    { name: 'Waiting', value: count('waiting'), color: COLORS.warn },
    { name: 'Failed', value: count('failed'), color: COLORS.bad },
  ]
  const total = todays.length
  const rate = total ? Math.round((data[0].value / total) * 100) : 0

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={total ? data : [{ name: 'None', value: 1, color: COLORS.track }]}
            dataKey="value"
            innerRadius={62}
            outerRadius={84}
            paddingAngle={total ? 3 : 0}
            stroke="none"
            animationDuration={900}
          >
            {(total ? data : [{ color: COLORS.track }]).map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Pie>
          {total > 0 && <Tooltip content={<ChartTooltip />} />}
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="text-3xl font-semibold tabular-nums">{rate}%</p>
          <p className="text-xs text-muted-foreground">paid</p>
        </div>
      </div>
      <div className="mt-2 flex justify-center gap-4 text-xs text-muted-foreground">
        {data.map((d) => (
          <span key={d.name} className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: d.color }} />
            {d.name} <b className="text-foreground tabular-nums">{d.value}</b>
          </span>
        ))}
      </div>
    </div>
  )
}

/** Horizontal bars: who spent the most today. */
export function TopSpendersChart({ perCard }: { perCard: CardSummary[] }) {
  const COLORS = useColors()
  const data = [...perCard]
    .filter((c) => c.spent > 0 || c.taps > 0)
    .sort((a, b) => b.spent - a.spent || b.taps - a.taps)
    .slice(0, 6)
    .map((c) => ({ name: c.name, Spent: c.spent, Taps: c.taps }))

  if (!data.length) return <p className="py-10 text-center text-sm text-muted-foreground">No card activity yet today.</p>

  return (
    <ResponsiveContainer width="100%" height={Math.max(140, data.length * 44)}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gBar" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={COLORS.brand} />
            <stop offset="100%" stopColor={COLORS.violet} />
          </linearGradient>
        </defs>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={90} tick={{ fill: COLORS.axis, fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip money={['Spent']} />} cursor={{ fill: COLORS.axis, fillOpacity: 0.08 }} />
        <Bar dataKey="Spent" fill="url(#gBar)" radius={[0, 8, 8, 0]} barSize={18} animationDuration={900} />
      </BarChart>
    </ResponsiveContainer>
  )
}
