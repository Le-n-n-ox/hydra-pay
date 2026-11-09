// Spoken announcements: "Payment received from Jeridah. 50 shillings."
// Uses the browser's built-in speech (no keys, works with the laptop or the cloud server).
// Browsers only allow speech after someone has clicked the page once, so the button shows when that's still needed.
import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Volume2, VolumeX } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Payment } from '@/lib/api'
import { cn } from '@/lib/utils'

const KEY = 'hydra-voice'
const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

function pickVoice() {
  const voices = window.speechSynthesis.getVoices()
  return (
    voices.find((v) => v.lang === 'en-KE') ||
    voices.find((v) => v.lang.startsWith('en') && /female|zira|aria|jenny|samantha|google uk english female/i.test(v.name)) ||
    voices.find((v) => v.lang.startsWith('en')) ||
    null
  )
}

export function speak(text: string) {
  if (!supported) return
  const u = new SpeechSynthesisUtterance(text)
  const v = pickVoice()
  if (v) u.voice = v
  u.rate = 0.95
  window.speechSynthesis.speak(u)
}

const spokenName = (p: Payment) => (p.name && p.name !== '—' ? p.name : 'a customer')
const spokenAmount = (n: number) => `${Math.round(Number(n) || 0).toLocaleString('en-US')} ${Number(n) === 1 ? 'shilling' : 'shillings'}`

/** Watches payments and speaks once when one turns PAID. Returns [enabled, setEnabled]. */
export function usePaymentVoice(payments: Payment[] | undefined) {
  const [enabled, setEnabledState] = useState(() => localStorage.getItem(KEY) !== 'off')
  const known = useRef<Map<number, string> | null>(null)

  const setEnabled = (on: boolean) => {
    setEnabledState(on)
    localStorage.setItem(KEY, on ? 'on' : 'off')
    if (supported) window.speechSynthesis.cancel()
    if (on) speak('Voice announcements on.')
  }

  useEffect(() => {
    if (!payments) return
    const prev = known.current
    const next = new Map(payments.map((p) => [p.id, p.status]))
    known.current = next
    if (!prev || !enabled) return   // first load: remember what's already paid, say nothing
    for (const p of [...payments].reverse()) {   // oldest first
      if (p.status === 'PAID' && prev.get(p.id) !== 'PAID') {
        speak(`Payment received from ${spokenName(p)}. ${spokenAmount(p.amount)}.`)
      }
    }
  }, [payments, enabled])

  // Some browsers load the voice list late.
  useEffect(() => {
    if (supported) window.speechSynthesis.onvoiceschanged = () => {}
  }, [])

  return [enabled, setEnabled] as const
}

/** Header button: turns announcements on/off and shows when a click is still needed to allow sound. */
export function VoiceToggle({ enabled, onChange }: { enabled: boolean; onChange: (on: boolean) => void }) {
  const [activated, setActivated] = useState(() => !!navigator.userActivation?.hasBeenActive)
  useEffect(() => {
    if (activated) return
    const done = () => setActivated(true)
    window.addEventListener('pointerdown', done, { once: true })
    window.addEventListener('keydown', done, { once: true })
    return () => {
      window.removeEventListener('pointerdown', done)
      window.removeEventListener('keydown', done)
    }
  }, [activated])

  if (!supported) return null
  const waiting = enabled && !activated
  const tip = !enabled ? 'Voice announcements off' : waiting ? 'Click anywhere once to allow sound' : 'Voice announcements on'
  return (
    <Tooltip>
      <TooltipTrigger
        render={<Button variant="outline" size="icon" aria-label={tip} aria-pressed={enabled} className={cn('glass relative rounded-full', waiting && 'ring-2 ring-amber-400/60')} />}
        onClick={() => onChange(!enabled)}
      >
        {waiting && <span className="absolute -right-0.5 -top-0.5 size-2.5 animate-ping-slow rounded-full bg-amber-400" />}
        <AnimatePresence mode="wait" initial={false}>
          <motion.span key={String(enabled)} initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.5, opacity: 0 }} className="grid place-items-center">
            {enabled ? <Volume2 className="size-4 text-good" /> : <VolumeX className="size-4 text-muted-foreground" />}
          </motion.span>
        </AnimatePresence>
      </TooltipTrigger>
      <TooltipContent>{tip}</TooltipContent>
    </Tooltip>
  )
}
