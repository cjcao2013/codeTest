import { render, screen } from '@testing-library/react'
import { ReportViewer } from './ReportViewer'

test('renders markdown headings', () => {
  render(<ReportViewer markdown={'# Hello\n\nWorld'} />)
  expect(screen.getByRole('heading', { name: 'Hello' })).toBeInTheDocument()
  expect(screen.getByText('World')).toBeInTheDocument()
})

test('renders empty state when markdown is null', () => {
  render(<ReportViewer markdown={null} />)
  expect(screen.getByText(/no report/i)).toBeInTheDocument()
})
