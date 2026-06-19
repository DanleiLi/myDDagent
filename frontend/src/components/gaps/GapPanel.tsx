import { ScrollArea } from '@/components/ui/scroll-area'
import { GapItem } from './GapItem'
import type { GapFlag } from '@/lib/api'

interface GapPanelProps {
  flags: GapFlag[]
  unresolvedCount: number
  onResolveFlag: (id: string) => void
}

export function GapPanel({ flags, unresolvedCount, onResolveFlag }: GapPanelProps) {
  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)' }}>
        <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>
          Follow-up Questions
        </h3>
        <span
          className="text-xs px-1.5 py-0.5 rounded-full font-medium"
          style={{
            backgroundColor: unresolvedCount > 0 ? '#f59e0b20' : 'rgba(255,255,255,0.04)',
            color: unresolvedCount > 0 ? '#f59e0b' : 'var(--text-secondary)',
          }}
        >
          {unresolvedCount}
        </span>
      </div>

      {flags.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            No gaps detected yet.
          </p>
        </div>
      ) : (
        <ScrollArea className="flex-1 min-h-0">
          <div className="px-4 py-2 flex flex-col gap-0">
            {flags.map((flag, i) => (
              <div key={flag.id}>
                {i > 0 && (
                  <div style={{ height: '1px', backgroundColor: 'var(--border)', opacity: 0.4, margin: '2px 0' }} />
                )}
                <GapItem flag={flag} onResolve={onResolveFlag} />
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  )
}
