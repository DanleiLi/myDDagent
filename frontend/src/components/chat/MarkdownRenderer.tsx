import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState } from 'react'

interface MarkdownRendererProps {
  content: string
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 px-2 py-0.5 rounded text-xs transition-opacity opacity-60 hover:opacity-100"
      style={{ backgroundColor: 'rgba(255,255,255,0.15)', color: 'var(--text-secondary)' }}
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ className, children, ...props }) {
          const isInline = !className
          const codeText = String(children).replace(/\n$/, '')

          if (isInline) {
            return (
              <code
                className="px-1 py-0.5 rounded text-xs font-mono"
                style={{ backgroundColor: 'rgba(255,255,255,0.1)', color: 'var(--text-primary)' }}
                {...props}
              >
                {children}
              </code>
            )
          }

          return (
            <div className="relative my-2">
              <pre
                className="p-3 pr-14 rounded-md text-xs overflow-x-auto font-mono"
                style={{ backgroundColor: 'rgba(0,0,0,0.3)', color: 'var(--text-primary)' }}
              >
                <code>{codeText}</code>
              </pre>
              <CopyButton text={codeText} />
            </div>
          )
        },
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--accent)', textDecoration: 'underline' }}
            >
              {children}
            </a>
          )
        },
        p({ children }) {
          return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
        },
        ul({ children }) {
          return <ul className="mb-2 pl-4 list-disc space-y-1">{children}</ul>
        },
        ol({ children }) {
          return <ol className="mb-2 pl-4 list-decimal space-y-1">{children}</ol>
        },
        h1({ children }) {
          return <h1 className="text-base font-semibold mb-2 mt-3">{children}</h1>
        },
        h2({ children }) {
          return <h2 className="text-sm font-semibold mb-2 mt-3">{children}</h2>
        },
        h3({ children }) {
          return <h3 className="text-sm font-medium mb-1 mt-2">{children}</h3>
        },
        blockquote({ children }) {
          return (
            <blockquote
              className="pl-3 py-0.5 my-2 italic"
              style={{ borderLeft: '2px solid var(--border)', color: 'var(--text-secondary)' }}
            >
              {children}
            </blockquote>
          )
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
