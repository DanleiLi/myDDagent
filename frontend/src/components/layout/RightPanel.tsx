import { GapPanel } from '@/components/gaps/GapPanel'
import { DocumentCard } from '@/components/documents/DocumentCard'
import { AnalysisOutputCard } from '@/components/documents/AnalysisOutputCard'
import { UploadZone } from '@/components/documents/UploadZone'
import { useAnalysisOutputs } from '@/hooks/useAnalysisOutputs'
import { useDocuments } from '@/hooks/useDocuments'
import type { GapFlag } from '@/lib/api'

interface RightPanelProps {
  projectId: string | null
  flags: GapFlag[]
  unresolvedCount: number
  onResolveFlag: (id: string) => void
}

export function RightPanel({ projectId, flags, unresolvedCount, onResolveFlag }: RightPanelProps) {
  const { documents, uploadDocument } = useDocuments(projectId)
  const { outputs } = useAnalysisOutputs(projectId)

  return (
    <div className="flex flex-col h-full" style={{ color: 'var(--text-primary)' }}>
      {/* Top 60% — gap panel */}
      <div
        className="flex flex-col overflow-hidden"
        style={{ flex: '0 0 60%', borderBottom: '1px solid var(--border)' }}
      >
        <GapPanel flags={flags} unresolvedCount={unresolvedCount} onResolveFlag={onResolveFlag} />
      </div>

      {/* Bottom 40% — documents */}
      <div className="flex flex-col overflow-hidden" style={{ flex: '0 0 40%' }}>
        <div
          className="px-4 py-3 flex-shrink-0"
          style={{ borderBottom: '1px solid var(--border)' }}
        >
          <h3
            className="text-xs font-semibold uppercase tracking-wide"
            style={{ color: 'var(--text-secondary)' }}
          >
            Documents
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
          <UploadZone onUpload={uploadDocument} disabled={!projectId} />
          {documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
          {outputs.length > 0 && (
            <div className="pt-3 flex flex-col gap-2">
              <h4
                className="text-[10px] font-semibold uppercase tracking-wide"
                style={{ color: 'var(--text-secondary)' }}
              >
                Analysis Outputs
              </h4>
              {outputs.map((output) => (
                <AnalysisOutputCard key={output.id} output={output} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
