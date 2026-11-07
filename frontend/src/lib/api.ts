// Types and fetch helpers for the Flask API in dashboard.py.

export type Card = {
  uid: string
  name: string
  phone: string
  price: number
  balance: number
  status: 'IN' | 'OUT'
  created: string
  blocked?: number
}

export type Scan = {
  id: number
  time: string
  uid: string
  direction: string
  result: string
  amount: number
  balance: number
}

export type Transaction = {
  id: number
  time: string
  uid: string
  kind: string
  amount: number
  balance_after: number
  note: string
  reversed: number
  ref: string
  label: string
}

export type Payment = {
  id: number
  time: string
  uid: string
  phone: string
  amount: number
  source: string
  status: string
  checkout_id: string
  tx_id: number | null
  name: string
  mpesa_receipt: string
}

export type CardSummary = {
  uid: string
  name: string
  phone: string
  balance: number
  taps: number
  paid_taps: number
  denied: number
  spent: number
  topped_up: number
}

export type Summary = {
  date: string
  mpesa: number
  swipe_paid: number
  swipe_unpaid: number
  cash: number
  tap_revenue: number
  taps: number
  denied: number
  per_card: CardSummary[]
}

export type DashboardData = {
  esp: { port: string | null; connected: boolean; message: string }
  services: {
    whatsapp: boolean
    gemini: boolean
    voice: boolean
    sms: boolean
    sms_provider: string
    ussd_provider: string
  }
  lan_url: string
  public_url: string
  cards: Card[]
  inside: Card[]
  new_card: string | null
  scans: Scan[]
  transactions: Transaction[]
  payments: Payment[]
  summary: Summary
  default_price: number
  mode: 'prompt' | 'wallet'
}

export type SmsRow = {
  id: number
  time: string
  phone: string
  kind: string
  text: string
  provider: string
  message_id: string
  status: string
  cost: string
  error: string
}

export type UssdSession = {
  session_id: string
  phone: string
  service_code: string
  provider: string
  started: string
  last_seen: string
  steps: string
  last_screen: string
  ended: number
}

export type TelcoSettings = {
  ussd_code: string
  admin_phone: string
  sms_receipts: boolean
  sms_when_whatsapp_fails: boolean
  sms_low_balance: boolean
  ussd_pin_required: boolean
}

export type TelcoStatus = {
  sms_provider: string
  ussd_provider: string
  ussd_code: string
  callbacks: { ussd?: string; delivery?: string; inbound?: string }
  sms: SmsRow[]
  sessions: UssdSession[]
  settings: Partial<TelcoSettings>
}

export type ApiResult = { ok?: boolean; message?: string; error?: string; [k: string]: unknown }

export class AuthError extends Error {}

export async function getJson<T>(url: string): Promise<T> {
  const r = await fetch(url, { credentials: 'same-origin' })
  if (r.status === 401) throw new AuthError('login required')
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json() as Promise<T>
}

export async function postJson(url: string, body: object): Promise<{ status: number; data: ApiResult }> {
  const r = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = (await r.json().catch(() => ({ error: 'Server error' }))) as ApiResult
  return { status: r.status, data }
}
