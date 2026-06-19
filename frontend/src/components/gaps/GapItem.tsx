import { Checkbox } from '@/components/ui/checkbox'
import type { GapFlag } from '@/lib/api'

interface GapItemProps {
  flag: GapFlag
  onResolve: (id: string) => void
}

const FLAG_TYPE_COLOURS: Record<GapFlag['flag_type'], string> = {
  gap:      '#f59e0b',
  conflict: '#f87171',
  missing:  '#60a5fa',
}

export function GapItem({ flag, onResolve }: GapItemProps) {
  return (
    <div
      className="flex items-start gap-2 py-1.5"
      style={{ opacity: flag.resolved ? 0.45 : 1 }}
    >
      <Checkbox
        checked={flag.resolved}
        onCheckedChange={() => !flag.resolved && onResolve(flag.id)}
        className="mt-0.5 flex-shrink-0"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span
            className="text-xs font-medium"
            style={{ color: FLAG_TYPE_COLOURS[flag.flag_type] }}
          >
            {flag.flag_type}
          </span>
          <span
            className="text-xs font-medium truncate"
            style={{
              color: 'var(--text-primary)',
              textDecoration: flag.resolved ? 'line-through' : 'none',
            }}
          >
            {flag.field_name}
          </span>
        </div>
        <p
          className="text-xs leading-snug"
          style={{
            color: 'var(--text-secondary)',
            textDecoration: flag.resolved ? 'line-through' : 'none',
          }}
        >
          {flag.description}
        </p>
      </div>
    </div>
  )
}
