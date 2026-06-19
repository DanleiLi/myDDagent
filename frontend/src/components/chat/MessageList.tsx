import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { MessageBubble } from './MessageBubble'
import { ToolIndicator } from './ToolIndicator'
import type { ChatMessage, ActiveToolCall } from '@/hooks/useChat'

interface MessageListProps {
  messages: ChatMessage[]
  activeToolCall: ActiveToolCall | null
  isStreaming: boolean
}

export function MessageList({ messages, activeToolCall, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeToolCall])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Ask a question about your documents
        </p>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1">
      <div className="py-4 flex flex-col gap-1">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && activeToolCall && (
          <ToolIndicator tool={activeToolCall.tool} />
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
