import { useCallback, useEffect, useRef, useState } from 'react'
import { env } from '@/lib/env'
import { getAccessToken } from '@/lib/supabase'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export interface ActiveToolCall {
  tool: string
}

const TOOL_LABELS: Record<string, string> = {
  retrieve_context: 'Searching documents',
  run_analysis_script: 'Running analysis',
  check_schema_coverage: 'Checking coverage',
  generate_final_report: 'Generating report',
  draft_report_section: 'Drafting section',
  query_database: 'Querying database',
}

export function getToolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool
}

export function useChat(projectId: string | null, onTurnComplete?: () => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [activeToolCall, setActiveToolCall] = useState<ActiveToolCall | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Reset when project changes
  useEffect(() => {
    abortRef.current?.abort()
    setMessages([])
    setIsStreaming(false)
    setActiveToolCall(null)
  }, [projectId])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!projectId || isStreaming || !content.trim()) return

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
      }
      const assistantMsgId = crypto.randomUUID()
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setActiveToolCall(null)

      const token = await getAccessToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      abortRef.current = new AbortController()

      try {
        const res = await fetch(`${env.apiBaseUrl}/api/chat/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ project_id: projectId, message: content }),
          signal: abortRef.current.signal,
        })

        if (!res.ok || !res.body) {
          throw new Error(`Stream failed: ${res.status}`)
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const jsonStr = line.slice(6).trim()
            if (!jsonStr) continue

            try {
              const event = JSON.parse(jsonStr) as Record<string, unknown>

              switch (event.type) {
                case 'text_delta':
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId
                        ? { ...m, content: m.content + (event.delta as string) }
                        : m,
                    ),
                  )
                  break

                case 'tool_use':
                  setActiveToolCall({ tool: event.tool as string })
                  break

                case 'gap_flag':
                  break

                case 'done':
                  setActiveToolCall(null)
                  onTurnComplete?.()
                  break

                case 'error':
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId
                        ? { ...m, content: `Error: ${event.message as string}` }
                        : m,
                    ),
                  )
                  break
              }
            } catch {
              // skip malformed event
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: 'Failed to get a response. Please try again.' }
                : m,
            ),
          )
        }
      } finally {
        setIsStreaming(false)
        setActiveToolCall(null)
      }
    },
    [projectId, isStreaming, onTurnComplete],
  )

  return { messages, sendMessage, isStreaming, activeToolCall }
}
