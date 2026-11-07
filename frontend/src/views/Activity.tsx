import { motion } from 'motion/react'
import { ArrowDownLeft, ArrowUpRight, History, Radio, RotateCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState, Panel, PersonAvatar, Pill, stagger } from '@/components/shared'
import { ExportMenu } from '@/views/Payments'
import { useAdmin } from '@/hooks/useAdmin'
import type { Card, Scan, Transaction } from '@/lib/api'
import { shortTime } from '@/lib/format'

const resultTone = (r: string) =>
  r === 'blocked' || r === 'low balance' || r.startsWith('prompt not sent') ? 'red' : r === 'paid' || r.includes('M-Pesa') ? 'green' : 'muted'

export function ActivityView({ scans, transactions, cards, reload }: { scans: Scan[]; transactions: Transaction[]; cards: Card[]; reload: () => void }) {
  const post = useAdmin()
  const names = new Map(cards.map((c) => [c.uid, c.name]))

  const undo = async (t: Transaction) => {
    if (!confirm(`Reverse ${t.label.toLowerCase()} of KSh ${t.amount} for ${names.get(t.uid) || t.uid}?`)) return
    if (await post(`/api/undo/${t.id}`)) reload()
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <Panel title="Activity" icon={History} bodyClassName="p-0" action={<ExportMenu />}>
        <Tabs defaultValue="taps" className="gap-0">
          <div className="border-b border-foreground/[0.06] px-5 py-3">
            <TabsList>
              <TabsTrigger value="taps"><Radio /> Card taps</TabsTrigger>
              <TabsTrigger value="wallet"><History /> Wallet history</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="taps">
            {scans.length ? (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="pl-5">Time</TableHead>
                    <TableHead>Card</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead className="pr-5 text-right">KSh</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scans.map((s, i) => (
                    <motion.tr key={s.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 15) * 0.02 }}
                      className="border-b border-foreground/[0.05] hover:bg-foreground/[0.03]">
                      <TableCell className="pl-5 text-muted-foreground tabular-nums">{shortTime(s.time)}</TableCell>
                      <TableCell>
                        <span className="flex items-center gap-2.5">
                          <PersonAvatar name={names.get(s.uid) || '?'} className="size-8 text-[11px]" />
                          <span>
                            <span className="block font-medium">{names.get(s.uid) || 'Unregistered'}</span>
                            <span className="font-mono text-[11px] text-muted-foreground">{s.uid}</span>
                          </span>
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="flex items-center gap-1.5 text-sm">
                          {s.direction === 'IN' ? <ArrowDownLeft className="size-4 text-good" /> : <ArrowUpRight className="size-4 text-muted-foreground" />}
                          {s.direction}
                        </span>
                      </TableCell>
                      <TableCell><Pill tone={resultTone(s.result)}>{s.result}</Pill></TableCell>
                      <TableCell className="pr-5 text-right tabular-nums">{s.amount || ''}</TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <EmptyState icon={Radio} title="No taps yet" hint="Every tap on the reader is logged here." />
            )}
          </TabsContent>

          <TabsContent value="wallet">
            {transactions.length ? (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="pl-5">Time</TableHead>
                    <TableHead>Ref</TableHead>
                    <TableHead>Card</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                    <TableHead className="pr-5" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((t) => (
                    <TableRow key={t.id} className={t.reversed ? 'opacity-50' : ''}>
                      <TableCell className="pl-5 text-muted-foreground tabular-nums">{shortTime(t.time)}</TableCell>
                      <TableCell className="font-mono text-xs text-brand-text">{t.ref}</TableCell>
                      <TableCell className="font-medium">{names.get(t.uid) || t.uid}</TableCell>
                      <TableCell>
                        <Pill tone={t.kind.startsWith('TOPUP') ? 'green' : t.kind === 'REVERSAL' ? 'amber' : 'blue'}>{t.label}</Pill>
                        {t.reversed ? <Pill className="ml-1">reversed</Pill> : null}
                      </TableCell>
                      <TableCell className={`text-right font-semibold tabular-nums ${t.amount >= 0 ? 'text-good' : 'text-bad'}`}>
                        {t.amount >= 0 ? '+' : ''}{t.amount}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{t.balance_after}</TableCell>
                      <TableCell className="pr-5 text-right">
                        {t.kind.startsWith('TOPUP') && !t.reversed && (
                          <Button size="xs" variant="outline" onClick={() => undo(t)}><RotateCcw /> Undo</Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <EmptyState icon={History} title="No wallet transactions" hint="Top-ups, tap charges and reversals appear here." />
            )}
          </TabsContent>
        </Tabs>
      </Panel>
    </motion.div>
  )
}
