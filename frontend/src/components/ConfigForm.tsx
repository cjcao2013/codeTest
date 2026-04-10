import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

export interface FieldDef {
  name: string
  label: string
  type: 'text' | 'toggle'
  required: boolean
  defaultValue?: string | boolean
  placeholder?: string
}

interface Props {
  fields: FieldDef[]
  onSubmit: (values: Record<string, string | boolean>) => void
  disabled: boolean
  submitLabel?: string
}

export function ConfigForm({ fields, onSubmit, disabled, submitLabel = 'Run' }: Props) {
  const [values, setValues] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(
      fields.map((f) => [f.name, f.defaultValue ?? (f.type === 'toggle' ? false : '')])
    )
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    for (const f of fields) {
      if (f.required && !values[f.name]) return
    }
    onSubmit(values)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {fields.map((f) => (
        <div key={f.name} className="space-y-1">
          {f.type === 'text' ? (
            <>
              <Label htmlFor={f.name}>{f.label}</Label>
              <Input
                id={f.name}
                value={values[f.name] as string}
                onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                placeholder={f.placeholder}
              />
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Switch
                aria-labelledby={`label-${f.name}`}
                checked={values[f.name] as boolean}
                onCheckedChange={(checked) => setValues((v) => ({ ...v, [f.name]: checked }))}
              />
              <Label id={`label-${f.name}`}>{f.label}</Label>
            </div>
          )}
        </div>
      ))}
      <Button type="submit" disabled={disabled} className="w-full">
        {disabled ? 'Running…' : submitLabel}
      </Button>
    </form>
  )
}
