import { MarkdownRenderer } from './MarkdownRenderer'
import type { ChatMessage } from '@/hooks/useChat'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end px-4 py-1">
        <div
          className="max-w-[75%] px-3 py-2 rounded-2xl text-sm leading-relaxed"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start px-4 py-1">
      <div
        className="max-w-[85%] text-sm"
        style={{ color: 'var(--text-primary)' }}
      >
        {message.content ? (
          <MarkdownRenderer content={message.content} />
        ) : (
          <span
            className="inline-block w-4 h-1 rounded animate-pulse"
            style={{ backgroundColor: 'var(--text-secondary)' }}
          />
        )}
      </div>
    </div>
  )
}
