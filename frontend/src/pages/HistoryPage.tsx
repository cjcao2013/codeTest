import { useEffect, useState } from 'react'
import { HistoryList } from '@/components/HistoryList'
import { ReportViewer } from '@/components/ReportViewer'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { fetchHistory, fetchRun } from '@/lib/api'
import type { RunRecord, RunDetail } from '@/lib/types'

export function HistoryPage() {
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [selected, setSelected] = useState<RunDetail | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    fetchHistory().then(setRuns).catch(console.error)
  }, [])

  const handleSelect = async (runId: string) => {
    const detail = await fetchRun(runId).catch(() => null)
    setSelected(detail)
    setOpen(true)
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Run History</h2>
      <HistoryList runs={runs} onSelect={handleSelect} />
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Run Report — {selected?.type}</DialogTitle>
          </DialogHeader>
          <ReportViewer markdown={selected?.report ?? null} />
        </DialogContent>
      </Dialog>
    </div>
  )
}
