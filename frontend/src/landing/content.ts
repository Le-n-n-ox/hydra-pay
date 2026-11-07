// All landing-page copy lives here so it can be edited without touching layout code.
// Written for business owners: short, plain words, no technical terms.

import { Bus, Nfc, Receipt, ShieldCheck, ShoppingBasket, Smartphone, UtensilsCrossed, Wallet, type LucideIcon } from 'lucide-react'

export const audiences: { icon: LucideIcon; title: string; body: string }[] = [
  { icon: UtensilsCrossed, title: 'Canteens & cafés', body: 'Serve the lunch rush faster.' },
  { icon: ShoppingBasket, title: 'Shops & market stalls', body: 'Track every sale without a notebook.' },
  { icon: Bus, title: 'Matatus & transport', body: 'Quick fares right at the door.' },
]

export const steps: { icon: LucideIcon; title: string; body: string }[] = [
  { icon: Nfc, title: 'Tap', body: 'Your customer taps their card.' },
  { icon: Smartphone, title: 'Pay', body: 'An M-Pesa request pops up on their phone.' },
  { icon: ShieldCheck, title: 'Confirm', body: 'They enter their PIN and Safaricom confirms.' },
  { icon: Receipt, title: 'Done', body: 'You get paid and the sale is saved. They get a receipt.' },
]

export const modes = {
  prompt: {
    label: 'Pay each time',
    icon: Smartphone,
    summary: 'Customers pay with M-Pesa every time they tap.',
    bullets: ['Nothing to set up for customers', 'Great for walk-in customers'],
  },
  wallet: {
    label: 'Prepaid card',
    icon: Wallet,
    summary: 'Customers top up once. Each tap takes from their balance, no PIN needed.',
    bullets: ['Fastest at busy times', 'Top up with M-Pesa or cash'],
  },
}

export type Mark = 'yes' | 'partial' | 'no'
export const compareColumns = ['Hydra Pay', 'Cash', 'Till number', 'Notebook', 'Card machine']
export const compareRows: { label: string; marks: Mark[] }[] = [
  { label: 'No change, nothing to type', marks: ['yes', 'no', 'partial', 'no', 'partial'] },
  { label: 'Payment checked with Safaricom', marks: ['yes', 'no', 'partial', 'no', 'yes'] },
  { label: 'Every sale saved automatically', marks: ['yes', 'no', 'partial', 'no', 'yes'] },
  { label: 'Daily totals ready', marks: ['yes', 'no', 'partial', 'partial', 'partial'] },
  { label: 'Receipt for the customer', marks: ['yes', 'no', 'yes', 'no', 'yes'] },
  { label: 'Works without a smartphone', marks: ['yes', 'yes', 'yes', 'yes', 'partial'] },
  { label: 'No cut taken from each sale', marks: ['yes', 'yes', 'partial', 'yes', 'no'] },
]
export const compareFootnote = 'Standard M-Pesa charges still apply.'

export const safety: [string, string][] = [
  ['No fake messages', 'A payment only counts when Safaricom confirms it.'],
  ['Clear records', 'Every payment keeps its M-Pesa code and time.'],
  ['Protected', 'Changes to cards and cash need your admin PIN.'],
]

export const proof = [
  { value: 27, label: 'test payments sent' },
  { value: 10, label: 'confirmed as paid' },
  { value: 15, label: 'correctly rejected' },
]
export const proofNote = 'From our M-Pesa test runs, October 2026.'
