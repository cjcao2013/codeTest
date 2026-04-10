import { render, screen, fireEvent } from '@testing-library/react'
import { HistoryList } from './HistoryList'
import type { RunRecord } from '@/lib/types'

const runs: RunRecord[] = [
  { run_id: 'abc', type: 'assess', status: 'success', started_at: '2026-01-01T10:00:00Z', ended_at: '2026-01-01T10:01:00Z', duration_seconds: 60 },
  { run_id: 'def', type: 'migrate', status: 'failed', started_at: '2026-01-01T11:00:00Z', ended_at: null, duration_seconds: null },
]

test('renders run type for each row', () => {
  render(<HistoryList runs={runs} onSelect={vi.fn()} />)
  expect(screen.getByText('assess')).toBeInTheDocument()
  expect(screen.getByText('migrate')).toBeInTheDocument()
})

test('calls onSelect with run_id when row clicked', () => {
  const onSelect = vi.fn()
  render(<HistoryList runs={runs} onSelect={onSelect} />)
  fireEvent.click(screen.getByText('assess').closest('tr')!)
  expect(onSelect).toHaveBeenCalledWith('abc')
})

test('renders empty state when no runs', () => {
  render(<HistoryList runs={[]} onSelect={vi.fn()} />)
  expect(screen.getByText(/no runs/i)).toBeInTheDocument()
})
