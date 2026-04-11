import { useState, useCallback } from 'react'
import { ConfigForm, type FieldDef } from '@/components/ConfigForm'
import { LogViewer } from '@/components/LogViewer'
import { ReportViewer } from '@/components/ReportViewer'
import { startMigrate, createWs, fetchRun } from '@/lib/api'
import type { WsMessage } from '@/lib/types'

const FIELDS: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true, placeholder: '/path/to/project' },
  { name: 'env', label: '.env File Path', type: 'text', required: false, defaultValue: '.env' },
  { name: 'dry_run', label: 'Dry Run (skip upload)', type: 'toggle', required: false, defaultValue: false },
  { name: 'upload_delay', label: 'Upload Delay (s)', type: 'number', required: false, defaultValue: 0.5 },
  { name: 'report_out', label: 'Report Output Path', type: 'text', required: false, defaultValue: './tap-migration-report.md' },
]

export function MigratePage() {
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
      const { run_id } = await startMigrate({
        project_dir: values.project_dir as string,
        env: (values.env as string) || undefined,
        dry_run: values.dry_run as boolean,
        upload_delay: values.upload_delay as number,
        report_out: (values.report_out as string) || undefined,
      })
      const ws = createWs(`/api/migrate/ws/${run_id}`)
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
        <h2 className="text-lg font-semibold">Migration</h2>
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
