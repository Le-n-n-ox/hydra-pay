import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import {
  Bot,
  CreditCard,
  Globe,
  History,
  LayoutDashboard,
  MessageSquare,
  Mic,
  Phone,
  PlugZap,
  Plus,
  Repeat,
  Smartphone,
  Usb,
  Wifi,
  type LucideIcon,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { CardDialog, MoveCardDialog, TopupDialog, type CardDraft } from '@/components/dialogs'
import { Background, StatusDot, TapCardGraphic } from '@/components/shared'
import { ModeToggle, ThemePicker } from '@/components/ThemeSwitcher'
import { useDashboard, useTelco } from '@/hooks/useDashboard'
import type { Card, DashboardData } from '@/lib/api'
import { cn } from '@/lib/utils'
import { ActivityView } from '@/views/Activity'
import { Cards } from '@/views/Cards'
import { Overview } from '@/views/Overview'
import { Payments } from '@/views/Payments'
import { Telco } from '@/views/Telco'

type View = 'overview' | 'payments' | 'cards' | 'activity' | 'telco'

const NAV: { id: View; label: string; Icon: LucideIcon; title: string; sub: string }[] = [
  { id: 'overview', label: 'Overview', Icon: LayoutDashboard, title: 'Overview', sub: "Today's money, taps and live activity" },
  { id: 'payments', label: 'Payments', Icon: Smartphone, title: 'M-Pesa payments', sub: 'Every prompt and its result from Safaricom' },
  { id: 'cards', label: 'Cards', Icon: CreditCard, title: 'Cards', sub: 'Registered people, prices and card status' },
  { id: 'activity', label: 'Activity', Icon: History, title: 'Activity', sub: 'Card taps and wallet history' },
  { id: 'telco', label: 'SMS & USSD', Icon: MessageSquare, title: 'SMS & USSD', sub: 'Providers, callbacks, test tools and settings' },
]

function Logo() {
  return (
    <div className="flex items-center gap-3">
      <motion.div
        whileHover={{ rotate: -8, scale: 1.05 }}
        className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 shadow-lg shadow-brand-1/40"
      >
        <svg viewBox="0 0 24 24" className="size-5 fill-none stroke-white" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="5" width="20" height="14" rx="3" />
          <path d="M2 10h20M6 15h4" />
        </svg>
      </motion.div>
      <div>
        <p className="text-gradient text-lg font-bold leading-tight tracking-tight">Hydra Pay</p>
        <p className="text-xs text-muted-foreground">Tap. Pay. Walk in.</p>
      </div>
    </div>
  )
}

function Sidebar({ view, setView, data }: { view: View; setView: (v: View) => void; data: DashboardData | null }) {
  return (
    <aside className="glass sticky top-4 hidden h-[calc(100vh-2rem)] w-64 shrink-0 flex-col rounded-2xl p-4 lg:flex">
      <Logo />
      <nav className="mt-8 grid gap-1" aria-label="Main">
        {NAV.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setView(id)}
            aria-current={view === id ? 'page' : undefined}
            className={cn('relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors', view === id ? 'text-foreground' : 'text-muted-foreground hover:bg-foreground/[0.04] hover:text-foreground')}
          >
            {view === id && (
              <motion.span layoutId="nav-active" className="absolute inset-0 rounded-xl bg-gradient-to-r from-brand-1/25 to-brand-2/10 ring-1 ring-brand-1/30" transition={{ type: 'spring', stiffness: 380, damping: 32 }} />
            )}
            <Icon className="relative size-4" />
            <span className="relative">{label}</span>
            {id === 'cards' && data && <span className="relative ml-auto text-xs tabular-nums text-muted-foreground">{data.cards.length}</span>}
          </button>
        ))}
      </nav>

      <div className="mt-auto space-y-4">
        <div className="rounded-2xl bg-gradient-to-br from-foreground/[0.06] to-foreground/[0.02] p-4 ring-1 ring-foreground/[0.08]">
          <TapCardGraphic className="mx-auto w-36" />
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Mode: <b className="capitalize text-foreground">{data?.mode ?? '…'}</b>
            <br />
            {data?.mode === 'wallet' ? 'Taps use a prepaid balance' : 'Each tap IN sends an M-Pesa prompt'}
          </p>
        </div>
        {data && (
          <div className="space-y-1.5 text-xs text-muted-foreground">
            <p className="flex items-center gap-2 truncate"><Wifi className="size-3.5 shrink-0" />{data.lan_url}</p>
            {data.public_url && <p className="flex items-center gap-2 truncate"><Globe className="size-3.5 shrink-0" />{data.public_url}</p>}
          </div>
        )}
      </div>
    </aside>
  )
}

function ServiceChips({ data, down }: { data: DashboardData; down: boolean }) {
  const sv = data.services
  const chips: { label: string; on: boolean; Icon: LucideIcon; tip: string }[] = [
    { label: 'WhatsApp', on: sv.whatsapp, Icon: MessageSquare, tip: sv.whatsapp ? 'WhatsApp bot and receipts on' : 'No UltraMsg keys in .env' },
    { label: 'SMS', on: sv.sms, Icon: Smartphone, tip: `Provider: ${sv.sms_provider}` },
    { label: 'USSD', on: sv.ussd_provider !== 'none', Icon: Phone, tip: `Provider: ${sv.ussd_provider}` },
    { label: 'AI', on: sv.gemini, Icon: Bot, tip: 'Gemini replies on WhatsApp' },
    { label: 'Voice', on: sv.voice, Icon: Mic, tip: 'ElevenLabs voice notes' },
  ]
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Tooltip>
        <TooltipTrigger
          render={
            <span className={cn('glass flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium', down ? 'text-bad' : data.esp.connected ? 'text-good' : 'text-warn')} />
          }
        >
          <StatusDot on={!down && data.esp.connected} warn={!down && !data.esp.connected} />
          <Usb className="size-3.5" />
          {down ? 'Server offline' : data.esp.connected ? `Reader on ${data.esp.port}` : 'Reader not connected'}
        </TooltipTrigger>
        <TooltipContent>{down ? 'dashboard.py is not answering' : data.esp.message}</TooltipContent>
      </Tooltip>
      {chips.map(({ label, on, Icon, tip }) => (
        <Tooltip key={label}>
          <TooltipTrigger render={<span className={cn('glass hidden items-center gap-1.5 rounded-full px-3 py-1.5 text-xs sm:flex', on ? 'text-foreground' : 'text-muted-foreground')} />}>
            <Icon className={cn('size-3.5', on ? 'text-good' : 'opacity-50')} />
            {label}
          </TooltipTrigger>
          <TooltipContent>{tip}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}

function NewCardBanner({ uid, hasCards, onRegister, onMove }: { uid: string; hasCards: boolean; onRegister: () => void; onMove: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
      className="relative mb-5 flex flex-wrap items-center gap-4 overflow-hidden rounded-2xl border border-amber-400/40 bg-gradient-to-r from-amber-500/15 via-orange-500/10 to-brand-2/15 p-4 backdrop-blur-xl"
    >
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
      <div className="relative grid size-12 place-items-center">
        <span className="absolute inset-0 rounded-full bg-amber-400/40 animate-ping-slow" />
        <span className="relative grid size-12 place-items-center rounded-full bg-gradient-to-br from-amber-400 to-orange-600 text-white"><PlugZap className="size-5" /></span>
      </div>
      <div className="relative flex-1">
        <p className="font-semibold">New card tapped</p>
        <p className="font-mono text-sm text-warn">{uid}</p>
      </div>
      <div className="relative flex flex-wrap gap-2">
        <Button variant="success" onClick={onRegister}><Plus /> Register it</Button>
        {hasCards && <Button variant="outline" onClick={onMove}><Repeat /> Move a person to this card</Button>}
      </div>
    </motion.div>
  )
}

function LoadingScreen({ down }: { down: boolean }) {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="flex flex-col items-center gap-6 text-center">
        <TapCardGraphic className="w-48" />
        {down ? (
          <div>
            <p className="font-semibold text-bad">The dashboard program is not running</p>
            <p className="mt-1 text-sm text-muted-foreground">Start it with <code className="text-foreground">start.bat</code> or <code className="text-foreground">python dashboard.py</code>.</p>
          </div>
        ) : (
          <div className="grid w-64 gap-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="mx-auto h-3 w-2/3" />
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const { data, down, fresh, reload } = useDashboard(2000)
  const { telco, reloadTelco } = useTelco(10000)
  const [view, setViewState] = useState<View>(() => {
    const h = location.hash.slice(1) as View
    return NAV.some((n) => n.id === h) ? h : 'overview'
  })
  const setView = (v: View) => {
    setViewState(v)
    history.replaceState(null, '', '#' + v)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  useEffect(() => {
    const onHash = () => {
      const h = location.hash.slice(1) as View
      if (NAV.some((n) => n.id === h)) setViewState(h)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const [cardDialog, setCardDialog] = useState<{ draft: CardDraft; editing: boolean } | null>(null)
  const [topupCard, setTopupCard] = useState<Card | null>(null)
  const [moveUid, setMoveUid] = useState<string | null>(null)

  if (!data)
    return (
      <>
        <Background />
        <div className="fixed right-4 top-4 flex gap-2"><ModeToggle /><ThemePicker /></div>
        <LoadingScreen down={down} />
      </>
    )

  const current = NAV.find((n) => n.id === view)!
  const openNew = (uid = '') => setCardDialog({ draft: { uid, name: '', phone: '', price: data.default_price }, editing: false })
  const openEdit = (c: Card) => setCardDialog({ draft: { uid: c.uid, name: c.name, phone: c.phone, price: c.price }, editing: true })

  return (
    <>
      <Background />
      <div className="mx-auto flex max-w-[1600px] gap-5 p-3 pb-24 sm:p-4 lg:pb-4 2xl:max-w-[118rem] 2xl:gap-6 2xl:p-6">
        <Sidebar view={view} setView={setView} data={data} />

        <main className="min-w-0 flex-1 overflow-x-clip">
          <header className="sticky top-0 z-20 -mx-3 mb-5 flex flex-wrap items-center justify-between gap-3 px-3 py-3 sm:-mx-4 sm:px-4 backdrop-blur-md lg:static lg:mx-0 lg:px-0 lg:py-0 lg:backdrop-blur-none">
            <div className="flex items-center gap-3">
              <div className="lg:hidden"><Logo /></div>
              <AnimatePresence mode="wait">
                <motion.div key={view} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className="hidden lg:block">
                  <h1 className="text-2xl font-semibold tracking-tight">{current.title}</h1>
                  <p className="text-sm text-muted-foreground">{current.sub}</p>
                </motion.div>
              </AnimatePresence>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <ServiceChips data={data} down={down} />
              <ModeToggle />
              <ThemePicker />
            </div>
          </header>

          <AnimatePresence>
            {data.new_card && !cardDialog && !moveUid && (
              <NewCardBanner key={data.new_card} uid={data.new_card} hasCards={data.cards.length > 0} onRegister={() => openNew(data.new_card!)} onMove={() => setMoveUid(data.new_card)} />
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            <motion.div key={view} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.25 }}>
              {view === 'overview' && <Overview data={data} />}
              {view === 'payments' && <Payments payments={data.payments} fresh={fresh} />}
              {view === 'cards' && (
                <Cards cards={data.cards} perCard={data.summary.per_card} mode={data.mode} onAdd={() => openNew()} onEdit={openEdit} onTopup={setTopupCard} reload={reload} />
              )}
              {view === 'activity' && <ActivityView scans={data.scans} transactions={data.transactions} cards={data.cards} reload={reload} />}
              {view === 'telco' && <Telco telco={telco} reload={reloadTelco} />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* mobile bottom navigation */}
      <nav aria-label="Main" className="glass fixed inset-x-3 bottom-3 z-30 flex justify-around rounded-2xl p-1.5 lg:hidden">
        {NAV.map(({ id, label, Icon }) => (
          <button key={id} onClick={() => setView(id)} aria-current={view === id ? 'page' : undefined}
            className={cn('relative flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[10px]', view === id ? 'text-foreground' : 'text-muted-foreground')}>
            {view === id && <motion.span layoutId="mnav-active" className="absolute inset-0 rounded-xl bg-primary/20" />}
            <Icon className="relative size-5" />
            <span className="relative">{label}</span>
          </button>
        ))}
      </nav>

      <CardDialog open={!!cardDialog} onOpenChange={(o) => !o && setCardDialog(null)} initial={cardDialog?.draft ?? { uid: '', name: '', phone: '', price: 1 }} editing={!!cardDialog?.editing} onSaved={reload} />
      <TopupDialog card={topupCard} onClose={() => setTopupCard(null)} onDone={reload} />
      <MoveCardDialog newUid={moveUid} cards={data.cards} onClose={() => setMoveUid(null)} onDone={reload} />
    </>
  )
}
