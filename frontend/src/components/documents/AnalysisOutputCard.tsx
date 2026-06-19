import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { AnalysisOutput } from '@/lib/api'
import { downloadAnalysisOutput } from '@/lib/api'

interface AnalysisOutputCardProps {
  output: AnalysisOutput
}

const STATUS_CONFIG: Record<
  AnalysisOutput['status'],
  { label: string; color: string; bg: string }
> = {
  running: { label: 'Running', color: '#60a5fa', bg: '#60a5fa20' },
  complete: { label: 'Complete', color: '#10a37f', bg: '#10a37f20' },
  error: { label: 'Error', color: '#f87171', bg: '#f8717120' },
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-AU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function AnalysisOutputCard({ output }: AnalysisOutputCardProps) {
  const config = STATUS_CONFIG[output.status]

  const handleDownload = async () => {
    try {
      await downloadAnalysisOutput(output.id)
    } catch (error) {
      console.error('Failed to download analysis output:', error)
    }
  }

  return (
    <div
      className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-md"
      style={{ backgroundColor: 'var(--bg-sidebar)' }}
    >
      <div className="flex-1 min-w-0">
        <p
          className="text-xs font-medium truncate"
          style={{ color: 'var(--text-primary)' }}
          title={output.script_name}
        >
          {output.script_name}
        </p>
        <p className="text-[11px]" style={{ color: 'var(--text-secondary)' }}>
          {formatDate(output.created_at)}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <span
          className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded-full font-medium"
          style={{ backgroundColor: config.bg, color: config.color }}
        >
          {config.label}
        </span>
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          onClick={handleDownload}
          aria-label={`Download ${output.script_name}`}
          disabled={output.status !== 'complete'}
          style={{ color: 'var(--text-secondary)' }}
        >
          <Download />
        </Button>
      </div>
    </div>
  )
}
