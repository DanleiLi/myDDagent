import type { Document } from '@/lib/api'

interface DocumentCardProps {
  document: Document
}

const STATUS_CONFIG: Record<
  Document['status'],
  { label: string; color: string; bg: string }
> = {
  uploading: { label: 'Uploading', color: '#60a5fa', bg: '#60a5fa20' },
  chunking:  { label: 'Processing', color: '#f59e0b', bg: '#f59e0b20' },
  embedded:  { label: 'Indexing', color: '#a78bfa', bg: '#a78bfa20' },
  ready:     { label: 'Ready', color: '#10a37f', bg: '#10a37f20' },
  error:     { label: 'Error', color: '#f87171', bg: '#f8717120' },
}

export function DocumentCard({ document }: DocumentCardProps) {
  const config = STATUS_CONFIG[document.status]

  return (
    <div
      className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-md"
      style={{ backgroundColor: 'var(--bg-sidebar)' }}
    >
      <div className="flex-1 min-w-0">
        <p
          className="text-xs font-medium truncate"
          style={{ color: 'var(--text-primary)' }}
          title={document.filename}
        >
          {document.filename}
        </p>
      </div>
      <span
        className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded-full font-medium"
        style={{ backgroundColor: config.bg, color: config.color }}
      >
        {config.label}
      </span>
    </div>
  )
}
