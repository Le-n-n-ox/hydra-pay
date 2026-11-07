import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Check, Copy, Delete, MessageSquare, Phone, PhoneCall, PhoneOff, Send, Settings2, Signal, Webhook } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, Panel, Pill, StatusDot, fadeUp, stagger } from '@/components/shared'
import { useAdmin } from '@/hooks/useAdmin'
import { type TelcoSettings, type TelcoStatus } from '@/lib/api'
import { shortTime } from '@/lib/format'

/* ---------- phone-style USSD simulator ---------- */

function UssdPhone({ code }: { code: string }) {
  const post = useAdmin()
  const [phone, setPhone] = useState('')
  const [steps, setSteps] = useState<string[] | null>(null) // null = not dialled
  const [input, setInput] = useState('')
  const [screen, setScreen] = useState<{ message: string; end: boolean } | null>(null)
  const [session, setSession] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async (next: string[], sid: string) => {
    setBusy(true)
    const data = await post('/api/ussd/simulate', { phone, text: next.join('*'), session_id: sid }, { quiet: true })
    setBusy(false)
    if (!data) {
      setSteps(null)
      return
    }
    setSteps(next)
    setScreen({ message: String(data.message ?? ''), end: !!data.end })
  }

  const dial = () => {
    if (!phone) return toast.error('Enter the phone number to simulate')
    const sid = 'sim-' + Math.random().toString(36).slice(2, 10)
    setSession(sid)
    setInput('')
    run([], sid)
  }
  const send = () => {
    if (!steps || screen?.end) return
    run([...steps, input], session)
    setInput('')
  }
  const hangUp = () => {
    setSteps(null)
    setScreen(null)
    setInput('')
  }
  const press = (k: string) => setInput((v) => (v + k).slice(0, 20))
  const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']
  const active = steps !== null

  return (
    <div className="mx-auto w-full max-w-[300px]">
      <div className="relative rounded-[2.6rem] bg-gradient-to-b from-slate-700 to-slate-900 p-3 shadow-2xl shadow-black/60 ring-1 ring-white/10">
        <div className="absolute left-1/2 top-3 z-10 h-5 w-24 -translate-x-1/2 rounded-full bg-black" />
        <div className="relative flex h-[300px] flex-col overflow-hidden rounded-[2rem] bg-gradient-to-b from-slate-950 to-indigo-950 px-4 pb-4 pt-9">
          <div className="mb-3 flex items-center justify-between text-[10px] text-white/60">
            <span>Safaricom</span>
            <span className="flex items-center gap-1"><Signal className="size-3" /> 4G</span>
          </div>
          <AnimatePresence mode="wait">
            {!active ? (
              <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
                <p className="font-mono text-2xl tracking-wider text-white">{code || '*XXX#'}</p>
                <p className="text-xs text-white/50">Enter a linked phone number below, then press call.</p>
              </motion.div>
            ) : (
              <motion.div key={steps!.length + (screen?.message ?? '')} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-1 flex-col rounded-2xl bg-white/95 p-3 text-slate-900 shadow-lg">
                <pre className="scrollbar-thin flex-1 overflow-y-auto whitespace-pre-wrap font-sans text-[13px] leading-snug">{busy ? 'Running USSD code…' : screen?.message}</pre>
                {!screen?.end ? (
                  <div className="mt-2 flex items-center gap-2 border-t border-slate-200 pt-2">
                    <input aria-label="USSD reply" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()}
                      className="min-w-0 flex-1 rounded-md bg-slate-100 px-2 py-1 font-mono text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    <button onClick={send} className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white">Send</button>
                  </div>
                ) : (
                  <button onClick={hangUp} className="mt-2 rounded-md bg-slate-200 py-1 text-xs font-semibold">OK</button>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="grid grid-cols-3 gap-2 px-3 pb-2 pt-4">
          {keys.map((k) => (
            <motion.button key={k} whileTap={{ scale: 0.88 }} onClick={() => (active ? press(k) : setPhone((p) => (p + k).replace(/[^\d]/g, '').slice(0, 12)))}
              className="h-10 rounded-full bg-white/10 font-mono text-lg text-white transition-colors hover:bg-white/20">
              {k}
            </motion.button>
          ))}
          <motion.button whileTap={{ scale: 0.88 }} aria-label="Hang up" onClick={hangUp} className="grid h-10 place-items-center rounded-full bg-rose-600 text-white"><PhoneOff className="size-4" /></motion.button>
          <motion.button whileTap={{ scale: 0.88 }} aria-label={active ? 'Send reply' : 'Dial'} onClick={active ? send : dial} className="grid h-10 place-items-center rounded-full bg-emerald-500 text-white"><PhoneCall className="size-4" /></motion.button>
          <motion.button whileTap={{ scale: 0.88 }} aria-label="Delete" onClick={() => (active ? setInput((v) => v.slice(0, -1)) : setPhone((p) => p.slice(0, -1)))} className="grid h-10 place-items-center rounded-full bg-white/10 text-white"><Delete className="size-4" /></motion.button>
        </div>
      </div>
      <div className="mt-4 grid gap-1.5">
        <Label htmlFor="sim-phone">Simulate as phone</Label>
        <Input id="sim-phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0712 345 678" inputMode="tel" disabled={active} />
      </div>
    </div>
  )
}

/* ---------- copyable callback URL ---------- */

function CopyField({ label, value }: { label: string; value?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="grid gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2 rounded-lg bg-black/25 px-3 py-2 ring-1 ring-foreground/10">
        <code className="min-w-0 flex-1 truncate font-mono text-xs text-brand-text">{value || 'Not available'}</code>
        {value && (
          <Button size="icon-xs" variant="ghost" aria-label={`Copy ${label}`} onClick={() => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>
            {copied ? <Check className="text-good" /> : <Copy />}
          </Button>
        )}
      </div>
    </div>
  )
}

/* ---------- page ---------- */

export function Telco({ telco, reload }: { telco: TelcoStatus | null; reload: () => void }) {
  const post = useAdmin()
  const [testPhone, setTestPhone] = useState('')
  const [testText, setTestText] = useState('Hydra Pay SMS test')
  const [cfg, setCfg] = useState<Partial<TelcoSettings>>({})
  const [loadedCfg, setLoadedCfg] = useState(false)

  useEffect(() => {
    if (telco?.settings && !loadedCfg) {
      setCfg(telco.settings)
      setLoadedCfg(true)
    }
  }, [telco, loadedCfg])

  const sendTest = async () => {
    if (await post('/api/sms/test', { phone: testPhone, text: testText })) reload()
  }
  const saveCfg = async () => {
    if (await post('/api/telco/settings', cfg, { quiet: true })) {
      toast.success('SMS & USSD settings saved')
      reload()
    }
  }

  const providers = [
    { label: 'SMS provider', value: telco?.sms_provider ?? '…', Icon: MessageSquare },
    { label: 'USSD provider', value: telco?.ussd_provider ?? '…', Icon: Phone },
  ]
  const toggles: { key: keyof TelcoSettings; label: string; desc: string }[] = [
    { key: 'sms_receipts', label: 'SMS receipts', desc: 'Text a receipt after every confirmed payment' },
    { key: 'sms_when_whatsapp_fails', label: 'SMS fallback', desc: 'Send by SMS when WhatsApp fails' },
    { key: 'sms_low_balance', label: 'Low-balance alerts', desc: 'Warn customers when their balance is low' },
    { key: 'ussd_pin_required', label: 'USSD PIN', desc: 'Ask for a PIN before money actions on USSD' },
  ]

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="grid gap-5 xl:grid-cols-[1fr_340px]">
      <div className="grid content-start gap-5">
        <motion.div variants={fadeUp} className="grid gap-4 sm:grid-cols-2">
          {providers.map(({ label, value, Icon }) => (
            <div key={label} className="glass flex items-center gap-4 rounded-2xl p-5">
              <div className="grid size-11 place-items-center rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 text-white shadow-lg shadow-brand-1/30"><Icon className="size-5" /></div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="text-lg font-semibold capitalize">{value}</p>
              </div>
              <StatusDot on={value !== 'none' && value !== '…'} />
            </div>
          ))}
        </motion.div>

        <Panel title="Callback URLs" icon={Webhook} action={telco?.ussd_code ? <Pill tone="blue">USSD {telco.ussd_code}</Pill> : null}>
          {telco?.callbacks?.ussd ? (
            <div className="grid gap-3">
              <CopyField label="USSD callback" value={telco.callbacks.ussd} />
              <CopyField label="SMS delivery reports" value={telco.callbacks.delivery} />
              <CopyField label="Inbound SMS" value={telco.callbacks.inbound} />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Set <code className="text-foreground">TELCO_CALLBACK_TOKEN</code> in .env and start ngrok to show the URLs to paste into your provider's portal.</p>
          )}
        </Panel>

        <Panel title="Send a test SMS" icon={Send}>
          <div className="grid gap-3 sm:grid-cols-[12rem_1fr_auto] sm:items-end">
            <div className="grid gap-1.5"><Label htmlFor="t-phone">Phone</Label><Input id="t-phone" value={testPhone} onChange={(e) => setTestPhone(e.target.value)} placeholder="0712 345 678" inputMode="tel" /></div>
            <div className="grid gap-1.5"><Label htmlFor="t-text">Message</Label><Input id="t-text" value={testText} onChange={(e) => setTestText(e.target.value)} /></div>
            <Button onClick={sendTest} disabled={!testPhone}><Send /> Send</Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{testText.length}/160 characters · emoji are removed before sending</p>
        </Panel>

        <Panel title="Settings" icon={Settings2} action={<Button size="sm" onClick={saveCfg}>Save settings</Button>}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5"><Label htmlFor="c-code">USSD code</Label><Input id="c-code" value={cfg.ussd_code ?? ''} onChange={(e) => setCfg({ ...cfg, ussd_code: e.target.value })} placeholder="*XXX*YY#" className="font-mono" /></div>
            <div className="grid gap-1.5"><Label htmlFor="c-admin">Admin SMS phone</Label><Input id="c-admin" value={cfg.admin_phone ?? ''} onChange={(e) => setCfg({ ...cfg, admin_phone: e.target.value })} placeholder="0712 345 678" inputMode="tel" /></div>
            {toggles.map((t) => (
              <label key={t.key} className="flex cursor-pointer items-center justify-between gap-4 rounded-xl bg-foreground/[0.03] p-3 ring-1 ring-foreground/[0.06] transition-colors hover:bg-foreground/[0.05]">
                <span>
                  <span className="block text-sm font-medium">{t.label}</span>
                  <span className="block text-xs text-muted-foreground">{t.desc}</span>
                </span>
                <Switch checked={!!cfg[t.key]} onCheckedChange={(v) => setCfg({ ...cfg, [t.key]: !!v })} />
              </label>
            ))}
          </div>
        </Panel>

        <div className="grid gap-5 lg:grid-cols-2">
          <Panel title="Recent SMS" icon={MessageSquare} bodyClassName="p-0">
            {telco?.sms?.length ? (
              <Table>
                <TableHeader><TableRow className="hover:bg-transparent"><TableHead className="pl-5">Time</TableHead><TableHead>Phone</TableHead><TableHead>Kind</TableHead><TableHead className="pr-5">Status</TableHead></TableRow></TableHeader>
                <TableBody>
                  {telco.sms.slice(0, 8).map((m) => (
                    <TableRow key={m.id} title={m.error || m.text}>
                      <TableCell className="pl-5 text-xs text-muted-foreground">{shortTime(m.time)}</TableCell>
                      <TableCell className="tabular-nums">{m.phone}</TableCell>
                      <TableCell>{m.kind}</TableCell>
                      <TableCell className="pr-5"><Pill tone={/DELIVERED|SENT|QUEUED/i.test(m.status) ? 'green' : /FAIL/i.test(m.status) ? 'red' : 'amber'}>{m.status}</Pill></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : <EmptyState icon={MessageSquare} title="No SMS yet" />}
          </Panel>
          <Panel title="Recent USSD sessions" icon={Phone} bodyClassName="p-0">
            {telco?.sessions?.length ? (
              <Table>
                <TableHeader><TableRow className="hover:bg-transparent"><TableHead className="pl-5">Phone</TableHead><TableHead>Code</TableHead><TableHead className="pr-5">Last seen</TableHead></TableRow></TableHeader>
                <TableBody>
                  {telco.sessions.slice(0, 8).map((s) => (
                    <TableRow key={s.session_id} title={s.last_screen}>
                      <TableCell className="pl-5 tabular-nums">{s.phone}</TableCell>
                      <TableCell className="font-mono text-xs">{s.service_code}</TableCell>
                      <TableCell className="pr-5 text-xs text-muted-foreground">{shortTime(s.last_seen)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : <EmptyState icon={Phone} title="No USSD sessions yet" />}
          </Panel>
        </div>
      </div>

      <motion.div variants={fadeUp} className="glass h-fit rounded-2xl p-5 xl:sticky xl:top-24">
        <h2 className="mb-1 flex items-center gap-2 font-semibold"><Phone className="size-4 text-primary" /> USSD simulator</h2>
        <p className="mb-5 text-sm text-muted-foreground">Test the menu exactly as a customer sees it, without a provider.</p>
        <UssdPhone code={telco?.ussd_code ?? ''} />
      </motion.div>
    </motion.div>
  )
}
