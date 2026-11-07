import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { KeyRound, ShieldCheck } from 'lucide-react'
import { motion } from 'motion/react'
import { toast } from 'sonner'

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
import { postJson, type ApiResult } from '@/lib/api'

type AdminPost = (url: string, body?: object, opts?: { quiet?: boolean }) => Promise<ApiResult | null>

const AdminContext = createContext<AdminPost | null>(null)

/**
 * Every admin action on the Flask API needs the admin PIN in the request body.
 * This provider asks for it once in a dialog, remembers it for the session (in memory only),
 * and asks again if the server rejects it.
 */
export function AdminProvider({ children }: { children: ReactNode }) {
  const pin = useRef<string | null>(null)
  const resolver = useRef<((pin: string | null) => void) | null>(null)
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState('')
  const [wrong, setWrong] = useState(false)

  const askPin = (retry: boolean) =>
    new Promise<string | null>((resolve) => {
      resolver.current = resolve
      setWrong(retry)
      setValue('')
      setOpen(true)
    })

  const finish = (result: string | null) => {
    setOpen(false)
    resolver.current?.(result)
    resolver.current = null
  }

  const post = useCallback<AdminPost>(async (url, body = {}, opts = {}) => {
    for (let attempt = 0; attempt < 3; attempt++) {
      if (!pin.current) {
        pin.current = await askPin(attempt > 0)
        if (!pin.current) return null
      }
      const { status, data } = await postJson(url, { ...body, pin: pin.current })
      if (status === 403 && /pin/i.test(data.error || '')) {
        pin.current = null
        continue
      }
      if (status >= 400 || data.error) {
        toast.error(data.error || `Request failed (${status})`)
        return null
      }
      if (!opts.quiet && data.message) toast.success(data.message)
      return data
    }
    toast.error('Wrong admin PIN')
    return null
  }, [])

  return (
    <AdminContext.Provider value={post}>
      {children}
      <Dialog open={open} onOpenChange={(o) => !o && finish(null)}>
        <DialogContent className="glass sm:max-w-sm">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (value) finish(value)
            }}
            className="grid gap-5"
          >
            <DialogHeader className="items-center text-center">
              <motion.div
                initial={{ scale: 0.6, rotate: -20, opacity: 0 }}
                animate={{ scale: 1, rotate: 0, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 16 }}
                className="mb-1 grid size-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-1 to-brand-2 shadow-lg shadow-brand-1/30"
              >
                <KeyRound className="size-7 text-white" />
              </motion.div>
              <DialogTitle>Admin PIN</DialogTitle>
              <DialogDescription>
                {wrong ? 'That PIN was wrong. Try again.' : 'Enter the admin PIN to make this change.'}
              </DialogDescription>
            </DialogHeader>
            <motion.div animate={wrong ? { x: [0, -10, 10, -6, 6, 0] } : {}} transition={{ duration: 0.4 }}>
              <Input
                autoFocus
                type="password"
                inputMode="numeric"
                autoComplete="current-password"
                aria-label="Admin PIN"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="h-12 text-center text-2xl tracking-[0.5em]"
                placeholder="••••"
              />
            </motion.div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => finish(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!value}>
                <ShieldCheck /> Unlock
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </AdminContext.Provider>
  )
}

export function useAdmin() {
  const ctx = useContext(AdminContext)
  if (!ctx) throw new Error('useAdmin must be used inside <AdminProvider>')
  return ctx
}
