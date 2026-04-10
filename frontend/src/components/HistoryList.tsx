import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { RunRecord } from '@/lib/types'

interface Props {
  runs: RunRecord[]
  onSelect: (runId: string) => void
}

export function HistoryList({ runs, onSelect }: Props) {
  if (runs.length === 0) {
    return <p className="text-zinc-400 text-sm py-4">No runs yet.</p>
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Started</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((r) => (
          <TableRow
            key={r.run_id}
            className="cursor-pointer hover:bg-zinc-100"
            onClick={() => onSelect(r.run_id)}
          >
            <TableCell className="font-mono text-xs">
              {new Date(r.started_at).toLocaleString()}
            </TableCell>
            <TableCell>{r.type}</TableCell>
            <TableCell>
              <Badge
                variant={
                  r.status === 'success' ? 'default'
                  : r.status === 'failed' ? 'destructive'
                  : 'secondary'
                }
              >
                {r.status}
              </Badge>
            </TableCell>
            <TableCell>
              {r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : '—'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
