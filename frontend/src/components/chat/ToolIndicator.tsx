import { getToolLabel } from '@/hooks/useChat'

interface ToolIndicatorProps {
  tool: string
}

export function ToolIndicator({ tool }: ToolIndicatorProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-1">
      <div
        className="w-3 h-3 rounded-full animate-pulse"
        style={{ backgroundColor: 'var(--accent)' }}
      />
      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
        {getToolLabel(tool)}…
      </span>
    </div>
  )
}
