import type { ReactNode } from 'react'

interface AppShellProps {
  sidebar: ReactNode
  children: ReactNode
  rightPanel: ReactNode
}

export function AppShell({ sidebar, children, rightPanel }: AppShellProps) {
  return (
    <div
      style={{ display: 'grid', gridTemplateColumns: '260px 1fr 340px', height: '100vh' }}
      className="overflow-hidden"
    >
      {/* Left — sidebar */}
      <aside
        className="flex flex-col overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-sidebar)' }}
      >
        {sidebar}
      </aside>

      {/* Centre — chat / main content (overflow managed by ChatPane internally) */}
      <main
        className="flex flex-col overflow-hidden"
        style={{ backgroundColor: 'var(--bg-primary)' }}
      >
        {children}
      </main>

      {/* Right — gaps + upload */}
      <div
        className="flex flex-col overflow-hidden"
        style={{ backgroundColor: 'var(--bg-primary)', borderLeft: '1px solid var(--border)' }}
      >
        {rightPanel}
      </div>
    </div>
  )
}
