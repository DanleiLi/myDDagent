import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer'
import * as api from '@/lib/api'
import { DEFAULT_REPORT_TEMPLATE } from '@/lib/defaultTemplate'

interface TemplateEditorProps {
  projectId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TemplateEditor({ projectId, open, onOpenChange }: TemplateEditorProps) {
  const [content, setContent] = useState(DEFAULT_REPORT_TEMPLATE)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open || !projectId) return

    let cancelled = false

    const loadTemplate = async () => {
      setLoading(true)
      try {
        const template = await api.getTemplate(projectId)
        if (!cancelled) setContent(template.content || DEFAULT_REPORT_TEMPLATE)
      } catch (error) {
        console.error('Failed to load template:', error)
        if (!cancelled) setContent(DEFAULT_REPORT_TEMPLATE)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadTemplate()

    return () => {
      cancelled = true
    }
  }, [open, projectId])

  const handleSave = async () => {
    if (!projectId) return
    setSaving(true)
    try {
      await api.updateTemplate(projectId, content)
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save template:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setContent(DEFAULT_REPORT_TEMPLATE)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="w-[min(1200px,calc(100vw-2rem))] max-w-[min(1200px,calc(100vw-2rem))] p-0 bg-[color:var(--bg-primary)] text-[color:var(--text-primary)]"
        showCloseButton
      >
        <div className="border-b px-6 py-4" style={{ borderColor: 'var(--border)' }}>
          <DialogHeader>
            <DialogTitle>Edit Template</DialogTitle>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              Update the report structure for this project.
            </p>
          </DialogHeader>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 min-h-[70vh]">
          <div className="border-r" style={{ borderColor: 'var(--border)' }}>
            <div className="px-4 py-2 border-b text-[10px] uppercase tracking-wide font-semibold" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              Markdown
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={loading}
              className="w-full h-[calc(70vh-2.5rem)] resize-none bg-transparent px-4 py-3 text-sm outline-none font-mono leading-6"
              style={{ color: 'var(--text-primary)' }}
            />
          </div>

          <div className="flex flex-col min-h-0">
            <div className="px-4 py-2 border-b text-[10px] uppercase tracking-wide font-semibold" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              Preview
            </div>
            <ScrollArea className="flex-1 min-h-0">
              <div className="px-4 py-3">
                <MarkdownRenderer content={content} />
              </div>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter className="border-t px-6 py-4" showCloseButton={false} style={{ borderColor: 'var(--border)' }}>
          <Button type="button" variant="ghost" onClick={handleReset} disabled={saving || loading}>
            Reset to Default
          </Button>
          <Button type="button" onClick={handleSave} disabled={saving || loading || !projectId}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
