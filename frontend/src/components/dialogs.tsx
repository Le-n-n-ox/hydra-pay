import { useEffect, useState, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { Banknote, CreditCard, Loader2, Repeat, Smartphone } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { PersonAvatar, TapCardGraphic } from '@/components/shared'
import { useAdmin } from '@/hooks/useAdmin'
import { type Card } from '@/lib/api'
import { cn } from '@/lib/utils'

function Field({ label, htmlFor, hint, children }: { label: string; htmlFor: string; hint?: string; children: ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

function DialogIcon({ children, tone = 'from-brand-1 to-brand-2 shadow-brand-1/30' }: { children: ReactNode; tone?: string }) {
  return (
    <motion.div
      initial={{ scale: 0.5, opacity: 0, rotate: -15 }}
      animate={{ scale: 1, opacity: 1, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 16 }}
      className={cn('mb-1 grid size-12 place-items-center rounded-2xl bg-gradient-to-br text-white shadow-lg', tone)}
    >
      {children}
    </motion.div>
  )
}

/* ---------- add / edit card ---------- */

export type CardDraft = { uid: string; name: string; phone: string; price: string | number }

export function CardDialog({ open, onOpenChange, initial, editing, onSaved }: {
  open: boolean
  onOpenChange: (o: boolean) => void
  initial: CardDraft
  editing: boolean
  onSaved: () => void
}) {
  const post = useAdmin()
  const [form, setForm] = useState(initial)
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (open) setForm(initial)
  }, [open, initial])
  const set = (k: keyof CardDraft) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    const ok = await post('/api/cards', form)
    setBusy(false)
    if (ok) {
      onOpenChange(false)
      onSaved()
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass sm:max-w-md">
        <form onSubmit={save} className="grid gap-5">
          <DialogHeader>
            <DialogIcon>
              <CreditCard className="size-6" />
            </DialogIcon>
            <DialogTitle>{editing ? `Edit ${initial.name}` : 'Register a card'}</DialogTitle>
            <DialogDescription>
              {editing ? 'Change the name, phone or price for this card.' : 'Tap a new card on the reader to fill in the UID automatically.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <Field label="Card UID" htmlFor="uid">
              <Input id="uid" value={form.uid} onChange={set('uid')} placeholder="C3 6E 01 28" disabled={editing} className="font-mono" autoFocus={!form.uid} />
            </Field>
            <Field label="Name" htmlFor="name">
              <Input id="name" value={form.name} onChange={set('name')} placeholder="e.g. John" autoFocus={!!form.uid} required />
            </Field>
            <div className="grid grid-cols-[1fr_8rem] gap-3">
              <Field label="Phone (M-Pesa / WhatsApp)" htmlFor="phone">
                <Input id="phone" value={form.phone} onChange={set('phone')} placeholder="07xx xxx xxx" inputMode="tel" />
              </Field>
              <Field label="KSh per tap" htmlFor="price">
                <Input id="price" value={form.price} onChange={set('price')} inputMode="numeric" />
              </Field>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="success" disabled={busy || !form.uid || !form.name}>
              {busy ? <Loader2 className="animate-spin" /> : <CreditCard />} Save card
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

/* ---------- top up ---------- */

export function TopupDialog({ card, onClose, onDone }: { card: Card | null; onClose: () => void; onDone: () => void }) {
  const post = useAdmin()
  const [method, setMethod] = useState<'mpesa' | 'cash'>('mpesa')
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (card) {
      setAmount('')
      setMethod('mpesa')
    }
  }, [card])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!card) return
    setBusy(true)
    let ok = false
    if (method === 'cash') ok = !!(await post('/api/topup/cash', { uid: card.uid, amount }))
    else {
      // Needs the admin PIN too, so nobody on the public link can send payment prompts.
      ok = !!(await post('/api/topup/mpesa', { uid: card.uid, amount }))
    }
    setBusy(false)
    if (ok) {
      onClose()
      onDone()
    }
  }

  const quick = [50, 100, 200, 500, 1000]
  const methods = [
    { id: 'mpesa' as const, label: 'M-Pesa prompt', Icon: Smartphone, desc: 'Admin PIN, then the customer confirms' },
    { id: 'cash' as const, label: 'Cash at desk', Icon: Banknote, desc: 'Needs admin PIN' },
  ]

  return (
    <Dialog open={!!card} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="glass sm:max-w-md">
        <form onSubmit={submit} className="grid gap-5">
          <DialogHeader>
            <DialogIcon tone="from-emerald-500 to-teal-600 shadow-emerald-500/30">
              <Banknote className="size-6" />
            </DialogIcon>
            <DialogTitle>Top up {card?.name}</DialogTitle>
            <DialogDescription>
              Current balance <b className="text-foreground">KSh {card?.balance ?? 0}</b>
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-2">
            {methods.map(({ id, label, Icon, desc }) => (
              <button
                key={id}
                type="button"
                onClick={() => setMethod(id)}
                className={cn(
                  'relative rounded-xl border p-3 text-left transition-colors',
                  method === id ? 'border-primary/60 bg-primary/10' : 'border-foreground/10 bg-foreground/[0.03] hover:bg-foreground/[0.06]',
                )}
              >
                {method === id && (
                  <motion.span layoutId="topup-method" className="absolute inset-0 rounded-xl ring-2 ring-primary/60" transition={{ type: 'spring', stiffness: 400, damping: 30 }} />
                )}
                <Icon className="mb-2 size-5 text-primary" />
                <p className="text-sm font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </button>
            ))}
          </div>

          <Field label="Amount (KSh)" htmlFor="amount">
            <Input id="amount" autoFocus value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ''))} inputMode="numeric" placeholder="200" className="h-11 text-lg" />
          </Field>
          <div className="flex flex-wrap gap-2">
            {quick.map((q) => (
              <Button key={q} type="button" size="sm" variant="outline" onClick={() => setAmount(String(q))}>
                {q}
              </Button>
            ))}
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="success" disabled={busy || !Number(amount)}>
              {busy ? <Loader2 className="animate-spin" /> : method === 'mpesa' ? <Smartphone /> : <Banknote />}
              {method === 'mpesa' ? 'Send prompt' : 'Add cash'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

/* ---------- move a person to a replacement card ---------- */

export function MoveCardDialog({ newUid, cards, onClose, onDone }: {
  newUid: string | null
  cards: Card[]
  onClose: () => void
  onDone: () => void
}) {
  const post = useAdmin()
  const [from, setFrom] = useState<string>('')
  useEffect(() => {
    if (newUid) setFrom(cards[0]?.uid ?? '')
  }, [newUid, cards])
  const person = cards.find((c) => c.uid === from)

  const move = async () => {
    if (!newUid || !person) return
    if (await post('/api/cards/move', { old_uid: person.uid, new_uid: newUid })) {
      onClose()
      onDone()
    }
  }

  return (
    <Dialog open={!!newUid} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="glass sm:max-w-md">
        <DialogHeader>
          <DialogIcon tone="from-amber-400 to-orange-600 shadow-amber-500/30">
            <Repeat className="size-6" />
          </DialogIcon>
          <DialogTitle>Replace a lost card</DialogTitle>
          <DialogDescription>
            Move a person and all their history to card <code className="font-mono text-foreground">{newUid}</code>. Their old card stops working.
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center justify-center gap-4 py-2">
          {person && <PersonAvatar name={person.name} className="size-12 text-sm" />}
          <motion.div animate={{ x: [0, 6, 0] }} transition={{ duration: 1.4, repeat: Infinity }}>
            <Repeat className="size-5 text-muted-foreground" />
          </motion.div>
          <TapCardGraphic className="w-24" pulse={false} />
        </div>
        <Select value={from} onValueChange={(v) => setFrom(String(v))} items={cards.map((c) => ({ value: c.uid, label: `${c.name} · ${c.phone || c.uid}` }))}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Choose a person" />
          </SelectTrigger>
          <SelectContent>
            {cards.map((c) => (
              <SelectItem key={c.uid} value={c.uid}>
                {c.name} · {c.phone || c.uid}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={move} disabled={!person}>
            <Repeat /> Move to new card
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
