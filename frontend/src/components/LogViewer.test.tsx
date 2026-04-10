import { render, screen } from '@testing-library/react'
import { LogViewer } from './LogViewer'

test('renders each log line', () => {
  render(<LogViewer lines={['line one', 'line two']} />)
  expect(screen.getByText('line one')).toBeInTheDocument()
  expect(screen.getByText('line two')).toBeInTheDocument()
})

test('renders empty state when no lines', () => {
  render(<LogViewer lines={[]} />)
  expect(screen.getByText(/waiting/i)).toBeInTheDocument()
})
