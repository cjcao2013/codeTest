import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

interface Props {
  markdown: string | null
  className?: string
}

export function ReportViewer({ markdown, className }: Props) {
  if (!markdown) {
    return (
      <div className={cn('rounded border p-6 text-zinc-400 text-sm flex items-center justify-center min-h-32', className)}>
        No report yet.
      </div>
    )
  }

  return (
    <div className={cn('prose prose-zinc prose-sm max-w-none rounded border p-6 overflow-y-auto max-h-96', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  )
}
