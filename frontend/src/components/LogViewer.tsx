import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

interface Props {
  lines: string[]
  className?: string
}

export function LogViewer({ lines, className }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (lines.length === 0) {
    return (
      <div className={cn('bg-zinc-950 rounded p-4 text-zinc-500 text-sm font-mono h-64 flex items-center justify-center', className)}>
        Waiting for output…
      </div>
    )
  }

  return (
    <div className={cn('bg-zinc-950 rounded p-4 text-green-400 text-sm font-mono h-64 overflow-y-auto', className)}>
      {lines.map((line, i) => (
        <div key={i} className="whitespace-pre-wrap">{line}</div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
