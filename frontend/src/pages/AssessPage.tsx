import { useState, useCallback } from 'react'
import { ConfigForm, type FieldDef } from '@/components/ConfigForm'
import { LogViewer } from '@/components/LogViewer'
import { ReportViewer } from '@/components/ReportViewer'
import { startAssess, createWs, fetchRun } from '@/lib/api'
import type { WsMessage } from '@/lib/types'

const FIELDS: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true, placeholder: '/path/to/project' },
  { name: 'report_out', label: 'Report Output Path', type: 'text', required: false, defaultValue: './tap-assessment-report.md' },
  { name: 'volume_threshold', label: 'Volume Threshold', type: 'text', required: false, defaultValue: 'small:500,medium:5000' },
]

export function AssessPage() {
  const [logs, setLogs] = useState<string[]>([])
  const [report, setReport] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async (values: Record<string, string | boolean>) => {
    setLogs([])
    setReport(null)
    setError(null)
    setRunning(true)
    try {
      const { run_id } = await startAssess({
        project_dir: values.project_dir as string,
        report_out: (values.report_out as string) || undefined,
        volume_threshold: (values.volume_threshold as string) || undefined,
      })
      const ws = createWs(`/api/assess/ws/${run_id}`)
      ws.onmessage = (e) => {
        const msg: WsMessage = JSON.parse(e.data)
        if (msg.type === 'log') {
          setLogs((l) => [...l, msg.line])
        } else if (msg.type === 'done') {
          fetchRun(run_id).then((r) => setReport(r.report))
          setRunning(false)
          ws.close()
        } else if (msg.type === 'error') {
          setError(msg.message)
          setRunning(false)
          ws.close()
        }
      }
      ws.onerror = () => {
        setError('WebSocket connection failed')
        setRunning(false)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setRunning(false)
    }
  }, [])

  return (
    <div className="grid grid-cols-[320px_1fr] gap-6">
      <aside className="space-y-4">
        <h2 className="text-lg font-semibold">Assessment</h2>
        <ConfigForm fields={FIELDS} onSubmit={handleSubmit} disabled={running} />
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </aside>
      <main className="space-y-4">
        <LogViewer lines={logs} />
        <ReportViewer markdown={report} />
      </main>
    </div>
  )
}
