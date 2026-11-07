import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Download, Search, Smartphone } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, Panel, PaymentBadge, PersonAvatar, stagger } from '@/components/shared'
import type { Payment } from '@/lib/api'
import { payState, shortTime, today, type PayState } from '@/lib/format'
import { cn } from '@/lib/utils'

export function ExportMenu() {
  const download = (what: string) => (location.href = `/api/export?what=${what}&date=${today()}`)
  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="outline" size="sm" />}>
        <Download /> Export
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel>Today as CSV (Excel)</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => download('payments')}>M-Pesa payments</DropdownMenuItem>
        <DropdownMenuItem onClick={() => download('transactions')}>Wallet transactions</DropdownMenuItem>
        <DropdownMenuItem onClick={() => download('scans')}>Card taps</DropdownMenuItem>
        <DropdownMenuItem onClick={() => download('summary')}>Per-card summary</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

const filters: { id: 'all' | PayState; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'paid', label: 'Paid' },
  { id: 'waiting', label: 'Waiting' },
  { id: 'failed', label: 'Failed' },
]

export function Payments({ payments, fresh }: { payments: Payment[]; fresh: Set<number> }) {
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState<'all' | PayState>('all')
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return payments.filter(
      (p) =>
        (filter === 'all' || payState(p.status) === filter) &&
        (!needle || [p.name, p.phone, p.mpesa_receipt, String(p.amount)].some((v) => (v || '').toLowerCase().includes(needle))),
    )
  }, [payments, q, filter])

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <Panel title="M-Pesa payments" icon={Smartphone} bodyClassName="p-0" action={<ExportMenu />}>
        <div className="flex flex-wrap items-center gap-3 border-b border-foreground/[0.06] px-5 py-3">
          <div className="relative min-w-52 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 z-10 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, phone or M-Pesa code" className="pl-9" />
          </div>
          <div className="flex rounded-lg bg-foreground/5 p-1 ring-1 ring-foreground/10">
            {filters.map((f) => (
              <button key={f.id} onClick={() => setFilter(f.id)} className={cn('relative rounded-md px-3 py-1 text-sm transition-colors', filter === f.id ? 'text-foreground' : 'text-muted-foreground hover:text-foreground')}>
                {filter === f.id && <motion.span layoutId="pay-filter" className="absolute inset-0 rounded-md bg-primary/25 ring-1 ring-primary/40" transition={{ type: 'spring', stiffness: 400, damping: 32 }} />}
                <span className="relative">{f.label}</span>
              </button>
            ))}
          </div>
        </div>
        {rows.length ? (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-5">Time</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead className="text-right">KSh</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="pr-5">M-Pesa code</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <AnimatePresence initial={false}>
                {rows.map((p) => (
                  <motion.tr
                    key={p.id}
                    layout
                    initial={fresh.has(p.id) ? { opacity: 0, x: -20, backgroundColor: 'rgba(52,211,153,0.25)' } : false}
                    animate={{ opacity: 1, x: 0, backgroundColor: 'rgba(52,211,153,0)' }}
                    transition={{ duration: 1.2 }}
                    className="border-b border-foreground/[0.05] transition-colors hover:bg-foreground/[0.03]"
                  >
                    <TableCell className="pl-5 text-muted-foreground tabular-nums">{shortTime(p.time)}</TableCell>
                    <TableCell>
                      <span className="flex items-center gap-2.5 font-medium">
                        <PersonAvatar name={p.name || p.phone} className="size-8 text-[11px]" />
                        {p.name || '—'}
                      </span>
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">{p.phone}</TableCell>
                    <TableCell className="text-right font-semibold tabular-nums">{p.amount}</TableCell>
                    <TableCell><PaymentBadge status={p.status} /></TableCell>
                    <TableCell className="pr-5 font-mono text-xs text-brand-text">{p.mpesa_receipt}</TableCell>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </TableBody>
          </Table>
        ) : (
          <EmptyState icon={Smartphone} title={payments.length ? 'No payments match' : 'No payments yet'} hint={payments.length ? 'Try a different search or filter.' : 'Tap a card to send the first M-Pesa prompt.'} />
        )}
      </Panel>
    </motion.div>
  )
}
