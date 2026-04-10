import { render, screen, fireEvent } from '@testing-library/react'
import { ConfigForm, type FieldDef } from './ConfigForm'

const fields: FieldDef[] = [
  { name: 'project_dir', label: 'Project Directory', type: 'text', required: true },
  { name: 'dry_run', label: 'Dry Run', type: 'toggle', required: false },
]

test('renders all fields', () => {
  render(<ConfigForm fields={fields} onSubmit={vi.fn()} disabled={false} />)
  expect(screen.getByLabelText('Project Directory')).toBeInTheDocument()
  expect(screen.getByLabelText('Dry Run')).toBeInTheDocument()
})

test('calls onSubmit with field values', () => {
  const onSubmit = vi.fn()
  render(<ConfigForm fields={fields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.change(screen.getByLabelText('Project Directory'), { target: { value: '/tmp/proj' } })
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).toHaveBeenCalledWith({ project_dir: '/tmp/proj', dry_run: false })
})

test('disables submit when disabled=true', () => {
  render(<ConfigForm fields={fields} onSubmit={vi.fn()} disabled={true} />)
  expect(screen.getByRole('button', { name: /running/i })).toBeDisabled()
})

test('blocks submit when required field is empty', () => {
  const onSubmit = vi.fn()
  render(<ConfigForm fields={fields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).not.toHaveBeenCalled()
})

test('renders number input for type number field', () => {
  const numberFields: FieldDef[] = [
    { name: 'delay', label: 'Upload Delay', type: 'number', required: false, defaultValue: 0 },
  ]
  render(<ConfigForm fields={numberFields} onSubmit={vi.fn()} disabled={false} />)
  const input = screen.getByLabelText('Upload Delay')
  expect(input).toHaveAttribute('type', 'number')
})

test('submits numeric value for number field', () => {
  const onSubmit = vi.fn()
  const numberFields: FieldDef[] = [
    { name: 'delay', label: 'Upload Delay', type: 'number', required: false, defaultValue: 0 },
  ]
  render(<ConfigForm fields={numberFields} onSubmit={onSubmit} disabled={false} />)
  fireEvent.change(screen.getByLabelText('Upload Delay'), { target: { value: '0.3' } })
  fireEvent.click(screen.getByRole('button', { name: /run/i }))
  expect(onSubmit).toHaveBeenCalledWith({ delay: '0.3' })
})
