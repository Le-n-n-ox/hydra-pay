import { useCallback, useEffect, useRef, useState } from 'react'

import { AuthError, getJson, type DashboardData, type TelcoStatus } from '@/lib/api'
import { today } from '@/lib/format'

/** Polls /api/data and tracks which payments are new since the last poll (for highlight animations). */
export function useDashboard(intervalMs = 2000) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [down, setDown] = useState(false)
  const [fresh, setFresh] = useState<Set<number>>(() => new Set())
  const seen = useRef<Set<number> | null>(null)

  const load = useCallback(async () => {
    try {
      const d = await getJson<DashboardData>('/api/data?date=' + today())
      const ids = d.payments.map((p) => p.id)
      if (seen.current === null) seen.current = new Set(ids)
      else {
        const added = ids.filter((id) => !seen.current!.has(id))
        if (added.length) {
          added.forEach((id) => seen.current!.add(id))
          setFresh(new Set(added))
        }
      }
      setData(d)
      setDown(false)
    } catch (e) {
      if (e instanceof AuthError) {
        location.href = '/login'
        return
      }
      setDown(true)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, intervalMs)
    return () => clearInterval(id)
  }, [load, intervalMs])

  return { data, down, fresh, reload: load }
}

export function useTelco(intervalMs = 10000) {
  const [telco, setTelco] = useState<TelcoStatus | null>(null)
  const load = useCallback(async () => {
    try {
      setTelco(await getJson<TelcoStatus>('/api/telco/status'))
    } catch {
      /* the main poll handles offline/login state */
    }
  }, [])
  useEffect(() => {
    load()
    const id = setInterval(load, intervalMs)
    return () => clearInterval(id)
  }, [load, intervalMs])
  return { telco, reloadTelco: load }
}
