import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { CheckCircle2, Clock, CreditCard, Loader2, RotateCcw, Smartphone, Wallet, XCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { AnimatedNumber, PersonAvatar } from '@/components/shared'
import { cn } from '@/lib/utils'

/** A self-contained simulation of the dashboard. No real API calls, no real money. */

type Row = { id: number; name: string; amount: number; status: 'waiting' | 'paid' | 'failed' | 'wallet'; time: string }
const PEOPLE = [
  { name: 'Amina W.', price: 50 },
  { name: 'Brian O.', price: 80 },
  { name: 'Wanjiru K.', price: 120 },
]
const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export function DemoSim() {
  const [mode, setMode] = useState<'prompt' | 'wallet'>('prompt')
  const [who, setWho] = useState(0)
  const [rows, setRows] = useState<Row[]>([])
  const [collected, setCollected] = useState(0)
  const [taps, setTaps] = useState(0)
  const [balance, setBalance] = useState(500)
  const [busy, setBusy] = useState(false)
  const [phone, setPhone] = useState<'idle' | 'prompt' | 'paid' | 'declined' | 'deducted'>('idle')
  const id = useRef(0)
  const timers = useRef<number[]>([])

  const later = (ms: number, fn: () => void) => timers.current.push(window.setTimeout(fn, ms))

  const tap = (decline = false) => {
    if (busy) return
    const p = PEOPLE[who]
    const rid = ++id.current
    setBusy(true)
    setTaps((t) => t + 1)
    if (mode === 'wallet') {
      setRows((r) => [{ id: rid, name: p.name, amount: p.price, status: 'wallet' as const, time: now() }, ...r].slice(0, 5))
      setBalance((b) => b - p.price)
      setCollected((c) => c + p.price)
      setPhone('deducted')
      later(1400, () => { setPhone('idle'); setBusy(false) })
      return
    }
    setRows((r) => [{ id: rid, name: p.name, amount: p.price, status: 'waiting' as const, time: now() }, ...r].slice(0, 5))
    later(500, () => setPhone('prompt'))
    later(2300, () => {
      setRows((r) => r.map((x) => (x.id === rid ? { ...x, status: decline ? 'failed' : 'paid' } : x)))
      setPhone(decline ? 'declined' : 'paid')
      if (!decline) setCollected((c) => c + p.price)
    })
    later(3800, () => { setPhone('idle'); setBusy(false) })
  }

  const reset = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
    setRows([]); setCollected(0); setTaps(0); setBalance(500); setPhone('idle'); setBusy(false)
  }

  const badge = {
    waiting: { cls: 'bg-amber-500/15 text-warn ring-amber-500/30', Icon: Clock, text: 'Waiting for PIN' },
    paid: { cls: 'bg-emerald-500/15 text-good ring-emerald-500/30', Icon: CheckCircle2, text: 'Paid' },
    failed: { cls: 'bg-rose-500/15 text-bad ring-rose-500/30', Icon: XCircle, text: 'Declined' },
    wallet: { cls: 'bg-brand-1/15 text-brand-text ring-brand-1/30', Icon: Wallet, text: 'From balance' },
  }

  return (
    <div className="glass overflow-hidden rounded-3xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-foreground/[0.06] px-5 py-3">
        <div className="flex rounded-lg bg-muted p-1">
          {(['prompt', 'wallet'] as const).map((m) => (
            <button key={m} onClick={() => { setMode(m); reset() }} className={cn('relative rounded-md px-3 py-1 text-sm', mode === m ? 'text-foreground' : 'text-muted-foreground')}>
              {mode === m && <motion.span layoutId="demo-mode" className="absolute inset-0 rounded-md bg-background shadow-sm ring-1 ring-foreground/10" />}
              <span className="relative flex items-center gap-1.5">{m === 'prompt' ? <Smartphone className="size-3.5" /> : <Wallet className="size-3.5" />}{m === 'prompt' ? 'Pay per tap' : 'Prepaid wallet'}</span>
            </button>
          ))}
        </div>
        <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-medium text-warn ring-1 ring-amber-500/30">Demo · no real money</span>
      </div>

      <div className="grid gap-6 p-5 lg:grid-cols-[1fr_15rem]">
        {/* mini dashboard */}
        <div className="grid content-start gap-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              ['Collected', collected, (n: number) => `KSh ${Math.round(n)}`],
              ['Taps', taps, (n: number) => String(Math.round(n))],
              [mode === 'wallet' ? `${PEOPLE[who].name.split(' ')[0]}'s balance` : 'Confirmed', mode === 'wallet' ? balance : rows.filter((r) => r.status === 'paid').length, (n: number) => (mode === 'wallet' ? `KSh ${Math.round(n)}` : String(Math.round(n)))],
            ].map(([label, value, fmt]) => (
              <div key={label as string} className="rounded-2xl bg-foreground/[0.04] p-3 ring-1 ring-foreground/[0.06]">
                <p className="truncate text-xs text-muted-foreground">{label as string}</p>
                <p className="text-xl font-semibold"><AnimatedNumber value={value as number} format={fmt as (n: number) => string} /></p>
              </div>
            ))}
          </div>
          <div className="min-h-[15rem] rounded-2xl bg-foreground/[0.03] p-2 ring-1 ring-foreground/[0.06]">
            {rows.length === 0 ? (
              <div className="grid h-56 place-items-center"><p className="max-w-xs text-center text-sm text-muted-foreground">Pick a customer and press <b className="text-foreground">Tap card</b> to see it land here.</p></div>
            ) : (
              <ul>
                <AnimatePresence initial={false}>
                  {rows.map((r) => {
                    const b = badge[r.status]
                    return (
                      <motion.li key={r.id} layout initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-3 rounded-xl px-2 py-2">
                        <PersonAvatar name={r.name} className="size-8 text-[11px]" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{r.name}</p>
                          <p className="text-xs text-muted-foreground">KSh {r.amount} · {r.time}</p>
                        </div>
                        <motion.span key={r.status} initial={{ scale: 0.7 }} animate={{ scale: 1 }} className={cn('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset', b.cls)}>
                          <b.Icon className={cn('size-3.5', r.status === 'waiting' && 'animate-spin [animation-duration:3s]')} />{b.text}
                        </motion.span>
                      </motion.li>
                    )
                  })}
                </AnimatePresence>
              </ul>
            )}
          </div>
        </div>

        {/* controls + customer phone */}
        <div className="grid content-start gap-3">
          <p className="text-xs font-medium text-muted-foreground">Customer</p>
          <div className="grid gap-1.5">
            {PEOPLE.map((p, i) => (
              <button key={p.name} onClick={() => !busy && setWho(i)} className={cn('flex items-center gap-2.5 rounded-xl p-2 text-left text-sm ring-1 transition-colors', who === i ? 'bg-primary/10 ring-primary/50' : 'ring-foreground/10 hover:bg-foreground/[0.04]')}>
                <PersonAvatar name={p.name} className="size-7 text-[10px]" />
                <span className="flex-1">{p.name}</span>
                <span className="text-xs text-muted-foreground">KSh {p.price}</span>
              </button>
            ))}
          </div>
          <Button onClick={() => tap(false)} disabled={busy} className="h-11">
            {busy ? <Loader2 className="animate-spin" /> : <CreditCard />} Tap card
          </Button>
          {mode === 'prompt' && (
            <Button variant="outline" size="sm" onClick={() => tap(true)} disabled={busy}>Tap, then cancel on phone</Button>
          )}
          <div className="relative h-20 overflow-hidden rounded-2xl bg-slate-900 p-3 text-white ring-1 ring-white/10">
            <AnimatePresence mode="wait">
              <motion.p key={phone} initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -14, opacity: 0 }} className="text-xs leading-snug">
                {phone === 'idle' && <span className="text-white/50">Customer's phone</span>}
                {phone === 'prompt' && <>📲 <b>M-PESA:</b> Pay KSh {PEOPLE[who].price} to HYDRA PAY? Enter PIN</>}
                {phone === 'paid' && <>✅ Paid. Receipt sent on WhatsApp.</>}
                {phone === 'declined' && <>❌ Cancelled. Not counted as paid.</>}
                {phone === 'deducted' && <>💳 KSh {PEOPLE[who].price} taken from their balance. No PIN needed.</>}
              </motion.p>
            </AnimatePresence>
          </div>
          <Button variant="ghost" size="sm" onClick={reset}><RotateCcw /> Reset demo</Button>
        </div>
      </div>
    </div>
  )
}
