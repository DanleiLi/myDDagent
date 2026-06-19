import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useProjects } from '@/hooks/useProjects'
import { supabase } from '@/lib/supabase'
import type { Project } from '@/lib/api'

interface SidebarProps {
  activeProjectId: string | null
  onSelectProject: (id: string) => void
}

const STATUS_COLOURS: Record<Project['status'], string> = {
  collecting: '#3b82f6',
  reviewing: '#f59e0b',
  complete: '#10a37f',
}

const STATUS_LABELS: Record<Project['status'], string> = {
  collecting: 'Collecting',
  reviewing: 'Reviewing',
  complete: 'Complete',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-AU', { month: 'short', year: 'numeric' })
}

export function Sidebar({ activeProjectId, onSelectProject }: SidebarProps) {
  const { projects, createProject, loading } = useProjects()
  const [creating, setCreating] = useState(false)

  const handleNewProject = async () => {
    const name = window.prompt('Project name:')?.trim()
    if (!name) return
    setCreating(true)
    try {
      const project = await createProject(name)
      onSelectProject(project.id)
    } catch (err) {
      console.error('Failed to create project:', err)
    } finally {
      setCreating(false)
    }
  }

  const handleSignOut = () => supabase.auth.signOut()

  return (
    <div className="flex flex-col h-full" style={{ color: 'var(--text-primary)' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-4"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <span
          className="text-sm font-semibold tracking-wide uppercase"
          style={{ color: 'var(--text-secondary)' }}
        >
          Projects
        </span>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleNewProject}
          disabled={creating}
          style={{ color: 'var(--accent)', fontSize: '0.75rem', padding: '2px 6px' }}
        >
          {creating ? '…' : '+ New'}
        </Button>
      </div>

      {/* Project list */}
      <nav className="flex-1 overflow-y-auto py-2">
        {loading ? (
          <p className="px-4 py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
            Loading…
          </p>
        ) : projects.length === 0 ? (
          <p className="px-4 py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
            No projects yet. Create one to get started.
          </p>
        ) : (
          projects.map((project) => {
            const isActive = project.id === activeProjectId
            const colour = STATUS_COLOURS[project.status]
            return (
              <button
                key={project.id}
                onClick={() => onSelectProject(project.id)}
                className="w-full text-left px-4 py-3 flex flex-col gap-1 transition-colors hover:opacity-80"
                style={{
                  backgroundColor: isActive ? 'rgba(255,255,255,0.06)' : 'transparent',
                  borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                }}
              >
                <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                  {project.name}
                </span>
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full font-medium"
                    style={{ backgroundColor: `${colour}20`, color: colour }}
                  >
                    {STATUS_LABELS[project.status]}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {formatDate(project.created_at)}
                  </span>
                </div>
              </button>
            )
          })
        )}
      </nav>

      {/* Footer */}
      <div
        className="px-4 py-4 flex items-center justify-between"
        style={{ borderTop: '1px solid var(--border)' }}
      >
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          Dossier v0.1
        </span>
        <button
          onClick={handleSignOut}
          className="text-xs transition-opacity hover:opacity-70"
          style={{ color: 'var(--text-secondary)' }}
        >
          Sign out
        </button>
      </div>
    </div>
  )
}
