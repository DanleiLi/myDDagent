import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useChat } from '@/hooks/useChat'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { TemplateEditor } from '@/components/template/TemplateEditor'

interface ChatPaneProps {
  projectId: string | null
  onTurnComplete?: () => void
}

export function ChatPane({ projectId, onTurnComplete }: ChatPaneProps) {
  const { messages, sendMessage, isStreaming, activeToolCall } = useChat(projectId, onTurnComplete)
  const [templateOpen, setTemplateOpen] = useState(false)

  if (!projectId) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Select a project to start chatting
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1">
      <div
        className="flex items-center justify-between px-5 py-4 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div>
          <p className="text-xs uppercase tracking-wide font-semibold" style={{ color: 'var(--text-secondary)' }}>
            Conversation
          </p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>
            Ask questions about the current project documents.
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setTemplateOpen(true)}
          disabled={!projectId}
          style={{ color: 'var(--text-primary)' }}
        >
          Edit Template
        </Button>
      </div>

      <MessageList
        messages={messages}
        activeToolCall={activeToolCall}
        isStreaming={isStreaming}
      />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
      <TemplateEditor projectId={projectId} open={templateOpen} onOpenChange={setTemplateOpen} />
    </div>
  )
}
