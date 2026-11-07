import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { BadgeCheck, CheckCheck, Lock, Signal, Wifi } from 'lucide-react'

import { cn } from '@/lib/utils'

/**
 * Looping story of one payment:
 * 0 idle → 1 card taps reader → 2 STK prompt → 3 PIN typed → 4 PAID (Safaricom) → 5 WhatsApp receipt
 */
const DURATIONS = [1400, 1300, 1500, 1300, 1700, 2600]

function Reader({ active }: { active: boolean }) {
  return (
    <div className="relative">
      {/* radio waves */}
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="absolute left-1/2 top-[38%] size-24 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-brand-1/50"
          initial={false}
          animate={active ? { scale: [0.6, 1.9], opacity: [0.8, 0] } : { scale: 0.6, opacity: 0 }}
          transition={{ duration: 1.4, repeat: active ? Infinity : 0, delay: i * 0.35, ease: 'easeOut' }}
        />
      ))}
      <div className="relative h-48 w-36 rounded-[1.6rem] bg-gradient-to-b from-slate-700 to-slate-900 p-3 shadow-2xl shadow-black/40 ring-1 ring-white/10">
        <div className="grid h-full place-items-center rounded-2xl bg-gradient-to-b from-slate-800 to-slate-950 ring-1 ring-inset ring-white/5">
          <svg viewBox="0 0 24 24" className={cn('size-12 fill-none transition-colors duration-300', active ? 'stroke-brand-1' : 'stroke-white/30')} strokeWidth={1.6} strokeLinecap="round">
            <path d="M8.5 16.5a5 5 0 0 0 0-9M12 19a8.5 8.5 0 0 0 0-14M15.5 21.5a12 12 0 0 0 0-19" />
          </svg>
          <div className="absolute bottom-6 flex items-center gap-1.5">
            <motion.span animate={{ backgroundColor: active ? 'rgb(52 211 153)' : 'rgb(71 85 105)', boxShadow: active ? '0 0 12px rgb(52 211 153)' : '0 0 0 transparent' }} className="size-2 rounded-full" />
            <span className="text-[9px] font-semibold tracking-[0.3em] text-white/50">HYDRA</span>
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-muted-foreground">Card reader</p>
    </div>
  )
}

function Card({ tapped }: { tapped: boolean }) {
  return (
    <motion.div
      className="absolute left-0 top-6 z-10 w-36"
      initial={false}
      animate={tapped ? { x: 96, y: 22, rotate: -6, scale: 0.92 } : { x: 0, y: 0, rotate: -14, scale: 1 }}
      transition={{ type: 'spring', stiffness: 120, damping: 14 }}
    >
      <div className="relative aspect-[1.586] overflow-hidden rounded-xl bg-gradient-to-br from-brand-1 via-brand-2 to-brand-3 p-2.5 shadow-xl shadow-brand-2/40">
        <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent animate-shimmer" />
        <div className="h-3.5 w-5 rounded bg-gradient-to-br from-amber-200 to-amber-500" />
        <div className="absolute bottom-2.5 left-2.5 text-[8px] font-medium tracking-widest text-white/85">AMINA W.</div>
        <div className="absolute bottom-2.5 right-2.5 text-[8px] font-bold tracking-widest text-white/85">HYDRA</div>
      </div>
    </motion.div>
  )
}

function PhoneScreen({ step }: { step: number }) {
  return (
    <div className="relative h-[21rem] w-44 rounded-[2rem] bg-gradient-to-b from-slate-700 to-slate-900 p-2 shadow-2xl shadow-black/40 ring-1 ring-white/10">
      <div className="absolute left-1/2 top-3 z-10 h-4 w-14 -translate-x-1/2 rounded-full bg-black" />
      <div className="relative h-full overflow-hidden rounded-[1.6rem] bg-gradient-to-b from-slate-900 to-slate-950 px-3 pt-8">
        <div className="mb-3 flex items-center justify-between text-[9px] text-white/60">
          <span>14:05</span>
          <span className="flex items-center gap-1"><Signal className="size-2.5" /><Wifi className="size-2.5" /></span>
        </div>
        <AnimatePresence mode="wait">
          {step <= 1 && (
            <motion.div key="lock" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="pt-10 text-center text-white">
              <p className="text-4xl font-light tabular-nums">14:05</p>
              <p className="mt-1 text-[10px] text-white/50">Friday, 7 November</p>
            </motion.div>
          )}
          {(step === 2 || step === 3) && (
            <motion.div key="stk" initial={{ opacity: 0, scale: 0.9, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ type: 'spring', stiffness: 260, damping: 22 }}
              className="mt-6 rounded-2xl bg-white p-3 text-slate-900 shadow-lg">
              <p className="text-[10px] font-semibold text-emerald-600">M-PESA</p>
              <p className="mt-1 text-[11px] leading-snug">Do you want to pay <b>KSh 50</b> to <b>HYDRA PAY CANTEEN</b>?</p>
              <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-slate-100 px-2 py-1.5">
                <Lock className="size-3 text-slate-400" />
                <div className="flex gap-1.5">
                  {[0, 1, 2, 3].map((i) => (
                    <motion.span key={i} className="size-2 rounded-full bg-slate-300" animate={step === 3 ? { backgroundColor: 'rgb(15 23 42)', scale: [1, 1.4, 1] } : {}} transition={{ delay: i * 0.22 }} />
                  ))}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-1.5 text-center text-[10px] font-semibold">
                <span className="rounded-md bg-slate-100 py-1">Cancel</span>
                <motion.span className="rounded-md bg-emerald-600 py-1 text-white" animate={step === 3 ? { scale: [1, 0.92, 1] } : {}} transition={{ delay: 1 }}>Send</motion.span>
              </div>
            </motion.div>
          )}
          {step >= 4 && (
            <motion.div key="ok" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mt-4 space-y-2">
              <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 15 }}
                className="rounded-2xl bg-white/95 p-2.5 text-slate-900">
                <p className="text-[9px] font-semibold text-emerald-600">M-PESA · now</p>
                <p className="text-[10px] leading-snug">QJK7X2LM Confirmed. Ksh50.00 paid to HYDRA PAY CANTEEN.</p>
              </motion.div>
              {step >= 5 && (
                <motion.div initial={{ x: 30, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: 'spring', stiffness: 220, damping: 18 }}
                  className="rounded-2xl rounded-tr-sm bg-emerald-700/90 p-2.5 text-white">
                  <p className="text-[9px] font-semibold text-emerald-200">WhatsApp · Hydra Pay</p>
                  <p className="text-[10px] leading-snug">🧾 Receipt RFP00042<br />Paid KSh 50 · M-Pesa QJK7X2LM<br />✅ Tapped IN</p>
                  <CheckCheck className="ml-auto mt-0.5 size-3 text-sky-300" />
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export function HeroGraphic() {
  const reduce = useReducedMotion()
  const [step, setStep] = useState(reduce ? 5 : 0)
  useEffect(() => {
    if (reduce) return
    const id = setTimeout(() => setStep((s) => (s + 1) % DURATIONS.length), DURATIONS[step])
    return () => clearTimeout(id)
  }, [step, reduce])

  const labels = ['Ready', 'Card tapped', 'M-Pesa prompt sent', 'Customer enters PIN', 'Confirmed by Safaricom', 'Receipt sent']

  return (
    <div className="relative mx-auto w-full max-w-xl">
      <div className="absolute inset-0 -z-10 rounded-[3rem] bg-gradient-to-br from-brand-1/20 via-transparent to-brand-2/20 blur-2xl" />
      <div className="flex items-end justify-center gap-4 max-sm:[zoom:0.8] sm:gap-10">
        <div className="relative w-56 pt-4">
          <Card tapped={step >= 1} />
          <div className="ml-16"><Reader active={step === 1} /></div>
        </div>
        <PhoneScreen step={step} />
      </div>

      {/* status pill under the scene */}
      <div className="mt-8 flex justify-center">
        <div className="glass flex items-center gap-3 rounded-full py-2 pl-2 pr-4 text-sm">
          <AnimatePresence mode="wait">
            <motion.span key={step >= 4 ? 'paid' : 'wait'} initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}
              className={cn('grid size-7 place-items-center rounded-full text-white', step >= 4 ? 'bg-emerald-500' : 'bg-gradient-to-br from-brand-1 to-brand-2')}>
              {step >= 4 ? <BadgeCheck className="size-4" /> : <span className="size-2 animate-pulse rounded-full bg-white" />}
            </motion.span>
          </AnimatePresence>
          <AnimatePresence mode="wait">
            <motion.span key={step} initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -8, opacity: 0 }} className="font-medium">
              {labels[step]}
            </motion.span>
          </AnimatePresence>
          <div className="ml-2 flex gap-1">
            {labels.map((_, i) => (
              <span key={i} className={cn('h-1.5 rounded-full transition-all duration-500', i <= step ? 'w-4 bg-primary' : 'w-1.5 bg-foreground/15')} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
