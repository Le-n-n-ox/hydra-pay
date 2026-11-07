// All landing-page copy lives here so it can be edited without touching layout code.
// Facts come from the project's pitch deck (pitch/HydraPay_Deck.html) and the code itself.

import {
  Ban,
  BarChart3,
  Bot,
  Bus,
  CircleDollarSign,
  ClipboardList,
  FileSpreadsheet,
  KeyRound,
  MessageSquare,
  Mic,
  Palette,
  Phone,
  Plug,
  Receipt,
  Repeat,
  RotateCcw,
  ShieldCheck,
  ShoppingBasket,
  Smartphone,
  UtensilsCrossed,
  Wallet,
  type LucideIcon,
} from 'lucide-react'

export const problems: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: CircleDollarSign,
    title: 'Cash slows everything',
    body: 'Counting money and finding change at every sale builds queues. Cash leaves no record and is a target for theft.',
  },
  {
    icon: Smartphone,
    title: 'Mobile money disputes',
    body: 'Fake confirmation SMSs, screenshots, reversals and "I\'ve sent it" arguments. Checking each payment holds up the queue.',
  },
  {
    icon: ClipboardList,
    title: "Records don't add up",
    body: "Sales sit in a notebook, the till and a phone inbox. At the end of the day owners can't reconcile what they earned.",
  },
]

export const stats = [
  { value: 99, suffix: '%', label: 'of surveyed small businesses run partly or wholly in cash' },
  { value: 86, suffix: '%', label: 'accepted digital payments by June 2023' },
]
export const statsSource = "Sources: FinAccess MSE Tracker Survey 2023; World Bank analysis of Kenya's mobile money market."

export const steps: { title: string; body: string; detail: string }[] = [
  {
    title: 'Tap',
    body: 'The customer taps a card, key tag or wristband on the reader at the counter or matatu door.',
    detail: 'ESP32 + RC522 reads the 13.56 MHz card and sends its ID to the Hydra Pay server.',
  },
  {
    title: 'M-Pesa prompt',
    body: "The price is sent as an M-Pesa STK push to the customer's phone, paid to the business till.",
    detail: 'No till number or amount to type: the prompt arrives already filled in.',
  },
  {
    title: 'Verify',
    body: 'The customer enters their PIN. Hydra Pay marks it PAID only when Safaricom confirms.',
    detail: 'Status comes from the Daraja API, so a forwarded SMS or a screenshot never counts as payment.',
  },
  {
    title: 'Record',
    body: 'Saved with amount, time and M-Pesa code. A receipt goes out and the dashboard updates live.',
    detail: 'Every payment lands in the ledger, the daily totals and the CSV reports automatically.',
  },
]

export const modes = {
  prompt: {
    label: 'Pay per tap',
    icon: Smartphone,
    summary: 'Every tap IN sends one M-Pesa prompt for the card\'s price. Tapping OUT is free.',
    bullets: ['Nothing to load in advance', 'Best for walk-in customers', 'Each payment confirmed by Safaricom'],
  },
  wallet: {
    label: 'Prepaid wallet',
    icon: Wallet,
    summary: 'Regulars top up once by M-Pesa or cash. Each tap deducts the price instantly.',
    bullets: ['Fastest at peak hours: no PIN per tap', 'Low-balance alerts and optional auto top-up', 'Cash top-ups and undo from the dashboard'],
  },
}

export const features: { icon: LucideIcon; title: string; body: string; wide?: boolean }[] = [
  { icon: ShieldCheck, title: 'Verified payments', body: "PAID only on Safaricom's answer: the callback, with a status check as backup. Each payment is recorded exactly once.", wide: true },
  { icon: BarChart3, title: 'Live dashboard', body: 'Money collected, taps, failed prompts, who is inside, with charts that update every two seconds.', wide: true },
  { icon: Receipt, title: 'WhatsApp receipts', body: 'A receipt with the M-Pesa code goes to the customer after every confirmed payment.' },
  { icon: MessageSquare, title: 'WhatsApp bot', body: 'Customers check their card and payments, or change their number, by chatting.' },
  { icon: Bot, title: 'AI assistant', body: 'Answers in English, Kiswahili and Sheng, powered by Gemini.' },
  { icon: Mic, title: 'Voice notes', body: 'Spoken thank-you and receipts with ElevenLabs, and voice messages understood.' },
  { icon: Phone, title: 'USSD for any phone', body: 'No smartphone or data needed: card details, payments and top-up from a short code.', wide: true },
  { icon: Smartphone, title: 'SMS receipts & alerts', body: 'SMS receipts, low-balance and security alerts, and a fallback when WhatsApp fails.' },
  { icon: Repeat, title: 'Lost card? One click', body: "Move a person and their full history to a new card. The old one stops working.", wide: true },
  { icon: Ban, title: 'Block cards', body: 'Block a lost or misused card instantly; taps are refused and the owner is alerted.' },
  { icon: RotateCcw, title: 'Cash top-ups & undo', body: 'Record cash at the desk. Undo writes a reversal entry, so nothing is ever deleted.' },
  { icon: FileSpreadsheet, title: 'Reports & CSV', body: 'Daily totals per card plus payments, taps and transactions as Excel-ready CSV.' },
  { icon: KeyRound, title: 'Admin PIN', body: 'A PIN guards cards, cash and undo. Remote login stays off until the default PIN is changed.' },
  { icon: Plug, title: 'Self-healing reader', body: 'Finds the USB port by itself and reconnects if the reader is unplugged.' },
  { icon: Palette, title: 'Your look', body: 'Light and dark modes with six colour themes, on laptop and phone.', wide: true },
]

export type Mark = 'yes' | 'partial' | 'no'
export const compareColumns = ['Hydra Pay', 'Cash', 'M-Pesa till / Paybill', 'Sales notebook', 'Card POS terminal']
export const compareRows: { label: string; marks: Mark[]; note?: string }[] = [
  { label: 'Fast at peak: no change to count, nothing to type', marks: ['yes', 'no', 'partial', 'no', 'partial'] },
  { label: 'Payment verified at the source', marks: ['yes', 'no', 'partial', 'no', 'yes'], note: 'Till SMSs can be faked or forwarded' },
  { label: 'Every sale recorded automatically', marks: ['yes', 'no', 'partial', 'no', 'yes'] },
  { label: 'Daily totals per customer, ready to reconcile', marks: ['yes', 'no', 'partial', 'partial', 'partial'] },
  { label: 'Receipt sent to the customer', marks: ['yes', 'no', 'yes', 'no', 'yes'] },
  { label: 'Works for customers without a smartphone', marks: ['yes', 'yes', 'yes', 'yes', 'partial'], note: 'POS needs a bank card' },
  { label: 'Low-cost hardware, no per-sale cut by the provider', marks: ['yes', 'yes', 'partial', 'yes', 'no'] },
]
export const compareFootnote =
  'Typical use, not every setup. Hydra Pay takes no cut of sales; standard M-Pesa transaction tariffs still apply to the payment itself.'

export const proof = [
  { value: 27, label: 'M-Pesa prompts sent through Daraja' },
  { value: 10, label: 'payments confirmed PAID by Safaricom' },
  { value: 15, label: 'declined or unanswered, correctly NOT PAID' },
]
export const proofNote = 'Daraja sandbox test runs, 22–23 Oct 2026.'

export const markets: { icon: LucideIcon; tag: string; title: string; body: string; need: string }[] = [
  { icon: UtensilsCrossed, tag: 'Pilot first', title: 'Canteens & cafeterias', body: 'Lunch-hour rush, fixed prices, regular customers.', need: 'Shorter checkout and accurate sales records.' },
  { icon: ShoppingBasket, tag: 'Pilot first', title: 'Market & retail traders', body: 'Mixed cash and M-Pesa every day.', need: 'Easy payment tracking without expensive software.' },
  { icon: Bus, tag: 'Next', title: 'Matatus & transport', body: 'Many small fares under time pressure. Tap IN to board.', need: 'Fast fare collection, confirmed fares, clear daily takings.' },
]

export const risks: [string, string][] = [
  ['Fake confirmations', "Status comes only from Safaricom's Daraja API. An unverified payment is never shown as PAID."],
  ['Reversals & disputes', 'Every payment keeps its M-Pesa code, status and time in an append-only audit trail.'],
  ['Sensitive data', "Admin PIN, keys kept out of code, minimal data stored; aligned with Kenya's Data Protection Act."],
]

