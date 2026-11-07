export const today = () =>
  new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10)

export const ksh = (n: number) => `KSh ${Math.round(Number(n) || 0).toLocaleString()}`

/** "2026-11-07 14:05:33" -> "14:05" */
export const hhmm = (t: string) => (t || '').slice(11, 16)

/** "2026-11-07 14:05:33" -> "07 Nov, 14:05" */
export const shortTime = (t: string) => {
  if (!t) return ''
  const d = new Date(t.replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return t
  return d.toLocaleString(undefined, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export const initials = (name: string) =>
  (name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join('') || '?'

/** Stable hue per name, so each person keeps the same avatar colour. */
export const hue = (name: string) => [...String(name)].reduce((a, c) => a + c.charCodeAt(0) * 7, 0) % 360

export type PayState = 'paid' | 'failed' | 'waiting'

export const payState = (s: string): PayState =>
  s === 'PAID' ? 'paid' : /^(FAILED|NOT PAID)/.test(s) ? 'failed' : 'waiting'

export const payLabel = (s: string) =>
  s === 'PAID'
    ? 'Paid'
    : s.startsWith('Prompt sent')
      ? 'Waiting for PIN'
      : s.startsWith('Sending')
        ? 'Sending…'
        : s.replace(/^NOT PAID: /, '').replace(/^FAILED: /, 'Failed: ')

/** Bucket rows with a "YYYY-MM-DD HH:MM:SS" time into hours of `day`. */
export function byHour<T extends { time: string }>(rows: T[], day: string, value: (r: T) => number) {
  const now = new Date()
  const lastHour = day === today() ? now.getHours() : 23
  const buckets = Array.from({ length: lastHour + 1 }, (_, h) => ({ hour: `${String(h).padStart(2, '0')}:00`, value: 0 }))
  for (const r of rows) {
    if (!r.time?.startsWith(day)) continue
    const h = Number(r.time.slice(11, 13))
    if (buckets[h]) buckets[h].value += value(r)
  }
  // Start the chart at the first active hour (min. 6 hours shown) so it isn't mostly empty.
  const first = buckets.findIndex((b) => b.value > 0)
  const start = first < 0 ? Math.max(0, lastHour - 5) : Math.min(first, Math.max(0, lastHour - 5))
  return buckets.slice(start)
}
