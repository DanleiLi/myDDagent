import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  ArrowDownAZ,
  ArrowDownWideNarrow,
  FileText,
  Funnel,
  Layers3,
  Loader2,
  Plus,
  SquarePen,
  Trash2,
  Upload,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { TemplateEditor } from '@/components/template/TemplateEditor'
import { useChat } from '@/hooks/useChat'
import { useCitation } from '@/hooks/useCitation'
import { useDocuments } from '@/hooks/useDocuments'
import { useGaps } from '@/hooks/useGaps'
import { useProjects } from '@/hooks/useProjects'
import { useReport } from '@/hooks/useReport'
import type { EvidenceChunk, GapFlag, Project, ReportCitation, ReportDetail } from '@/lib/api'

type NavItem = 'reports' | 'templates' | 'data diagnostics'
type SortKey = 'created_at' | 'name' | 'status'
type Step = 1 | 2 | 3

const NAV_ITEMS: Array<{
  id: NavItem
  label: string
  icon: typeof Layers3
  disabled?: boolean
  tooltip?: string
}> = [
  { id: 'reports', label: 'Reports', icon: Layers3 },
  { id: 'templates', label: 'Templates', icon: SquarePen },
  { id: 'data diagnostics', label: 'Data Diagnostics', icon: Funnel, disabled: true, tooltip: 'Data diagnostics functionality is not implemented yet' },
]

const STEP_LABELS: Record<Step, string> = {
  1: 'Upload',
  2: 'Data quality',
  3: 'Report',
}

const PROJECT_STATUS_LABELS: Record<Project['status'], string> = {
  collecting: 'Collecting',
  reviewing: 'Reviewing',
  complete: 'Complete',
}

const PROJECT_STATUS_COLOURS: Record<Project['status'], string> = {
  collecting: '#1d6fb8',
  reviewing: '#b45309',
  complete: '#166534',
}

const DOCUMENT_STATUS_LABELS: Record<string, string> = {
  uploading: 'Uploading',
  chunking: 'Chunking',
  embedded: 'Embedded',
  ready: 'Ready',
  error: 'Error',
}

function formatDateTime(iso: string) {
  return new Intl.DateTimeFormat('en-AU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso))
}

function formatProjectSortValue(project: Project, sortKey: SortKey) {
  switch (sortKey) {
    case 'name':
      return project.name.toLowerCase()
    case 'status':
      return project.status
    case 'created_at':
    default:
      return project.created_at
  }
}

function statusPillClass(status: string) {
  switch (status) {
    case 'ready':
    case 'complete':
      return 'bg-emerald-500/15 text-emerald-700'
    case 'error':
      return 'bg-rose-500/15 text-rose-700'
    case 'reviewing':
    case 'chunking':
      return 'bg-amber-500/15 text-amber-700'
    case 'collecting':
    case 'uploading':
      return 'bg-sky-500/15 text-sky-700'
    default:
      return 'bg-black/[0.05] text-[color:var(--text-secondary)]'
  }
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string
  value: number
  detail?: string
}) {
  return (
    <div className="rounded-2xl border border-black/10 bg-black/[0.04] p-4 shadow-[0_1px_0_rgba(0,0,0,0.04)_inset]">
      <div className="text-[10px] uppercase tracking-[0.28em] text-[color:var(--text-secondary)]">
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold text-[color:var(--text-primary)]">{value}</div>
      {detail ? (
        <div className="mt-2 text-xs leading-relaxed text-[color:var(--text-secondary)]">
          {detail}
        </div>
      ) : null}
    </div>
  )
}

function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="rounded-3xl border border-dashed border-black/[0.12] bg-black/[0.03] p-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-black/[0.06] text-[color:var(--text-secondary)]">
        <FileText className="h-5 w-5" />
      </div>
      <div className="mt-4 text-sm font-semibold text-[color:var(--text-primary)]">{title}</div>
      <div className="mt-2 text-sm leading-relaxed text-[color:var(--text-secondary)]">
        {description}
      </div>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}

function SidebarNavButton({
  label,
  icon: Icon,
  active,
  disabled,
  expanded,
  onClick,
  tooltip,
}: {
  label: string
  icon: typeof Layers3
  active: boolean
  disabled?: boolean
  expanded: boolean
  onClick: () => void
  tooltip?: string
}) {
  const button = (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={[
        'flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-sm transition-all',
        active
          ? 'bg-black/[0.08] text-[color:var(--text-primary)]'
          : 'text-[color:var(--text-secondary)] hover:bg-black/[0.05] hover:text-[color:var(--text-primary)]',
        disabled ? 'cursor-not-allowed opacity-50' : '',
      ].join(' ')}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {expanded ? <span className="truncate">{label}</span> : null}
    </button>
  )

  if (!expanded || disabled) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{button}</TooltipTrigger>
        <TooltipContent>{tooltip ?? label}</TooltipContent>
      </Tooltip>
    )
  }

  return button
}

function ProjectRow({
  project,
  active,
  onSelect,
  onDelete,
}: {
  project: Project
  active: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect()
        }
      }}
      className={[
        'group w-full rounded-2xl border px-4 py-3 text-left transition-all',
        active
          ? 'border-black/[0.15] bg-black/[0.07]'
          : 'border-transparent bg-black/[0.03] hover:border-black/[0.12] hover:bg-black/[0.05]',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-[color:var(--text-primary)]">
            {project.name}
          </div>
          <div className="mt-1 text-xs text-[color:var(--text-secondary)]">
            {formatDateTime(project.created_at)}
          </div>
        </div>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation()
            onDelete()
          }}
          className="rounded-lg p-1.5 text-[color:var(--text-secondary)] opacity-0 transition group-hover:opacity-100 hover:bg-black/[0.06] hover:text-rose-700"
          aria-label={`Delete ${project.name}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <Badge
          className="rounded-full border-0 px-2 py-1"
          style={{
            backgroundColor: `${PROJECT_STATUS_COLOURS[project.status]}20`,
            color: PROJECT_STATUS_COLOURS[project.status],
          }}
        >
          {PROJECT_STATUS_LABELS[project.status]}
        </Badge>
      </div>
    </div>
  )
}

function FlagRow({
  flag,
  onResolve,
}: {
  flag: {
    id: string
    field_name: string
    description: string
    resolved: boolean
    flag_type: 'gap' | 'conflict' | 'missing'
  }
  onResolve: (id: string) => void
}) {
  return (
    <label
      className={[
        'flex items-start gap-3 rounded-2xl border px-4 py-3 transition-all',
        flag.resolved
          ? 'border-black/10 bg-black/[0.03] opacity-55'
          : 'border-black/[0.12] bg-black/[0.04]',
      ].join(' ')}
    >
      <Checkbox
        checked={flag.resolved}
        onCheckedChange={() => {
          if (!flag.resolved) onResolve(flag.id)
        }}
        className="mt-0.5"
      />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.28em] ${statusPillClass(flag.flag_type)}`}>
            {flag.flag_type}
          </span>
          <span className="text-sm font-medium text-[color:var(--text-primary)]">
            {flag.field_name}
          </span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-[color:var(--text-secondary)]">
          {flag.description}
        </p>
        {flag.resolved ? (
          <div className="mt-2 text-[10px] uppercase tracking-[0.3em] text-emerald-700">
            Resolved
          </div>
        ) : null}
      </div>
    </label>
  )
}

function WorkspacePageBody() {
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null)
  const [activeNav, setActiveNav] = useState<NavItem>('reports')
  const [sidebarPinned, setSidebarPinned] = useState(false)
  const [sidebarHovered, setSidebarHovered] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('created_at')
  const [sortDescending, setSortDescending] = useState(true)
  const [selectedStep, setSelectedStep] = useState<Step>(1)
  const [templateOpen, setTemplateOpen] = useState(false)
  const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null)
  const reportStepInitRef = useRef<string | null>(null)

  const { projects, createProject, deleteProject, loading: projectsLoading, refresh: refreshProjects } = useProjects()
  const {
    documents,
    allReady,
    uploading,
    uploadFiles,
    retryUpload,
    refresh: refreshDocuments,
  } = useDocuments(activeProjectId)
  const {
    groupedFlags,
    criteriaChecked,
    passed,
    needsReview,
    resolveFlag,
    refresh: refreshGaps,
  } = useGaps(activeProjectId)
  const {
    report,
    generating,
    hasReport,
    createReport,
    downloadCurrentReport,
    refresh: refreshReport,
  } = useReport(activeProjectId)
  const { messages, sendMessage, isStreaming, activeToolCall } = useChat(activeProjectId, () => {
    void Promise.all([refreshGaps(), refreshReport(), refreshDocuments()])
  })

  useEffect(() => {
    if (!projects.length) {
      setActiveProjectId(null)
      return
    }

    if (!activeProjectId || !projects.some((project) => project.id === activeProjectId)) {
      setActiveProjectId(projects[0].id)
    }
  }, [activeProjectId, projects])

  useEffect(() => {
    setSelectedCitationId(null)
    setSelectedStep(1)
    reportStepInitRef.current = null
  }, [activeProjectId])

  useEffect(() => {
    if (activeProjectId && hasReport && reportStepInitRef.current !== activeProjectId) {
      setSelectedStep(3)
      reportStepInitRef.current = activeProjectId
    }
  }, [activeProjectId, hasReport])

  useEffect(() => {
    if (!templateOpen || activeNav !== 'templates') return
    if (!activeProjectId) setTemplateOpen(false)
  }, [activeNav, activeProjectId, templateOpen])

  const sidebarExpanded = sidebarPinned || sidebarHovered
  const displayedProjects = useMemo(() => {
    const sorted = [...projects].sort((left, right) => {
      const leftValue = formatProjectSortValue(left, sortKey)
      const rightValue = formatProjectSortValue(right, sortKey)
      const comparison = leftValue.localeCompare(rightValue)
      return sortDescending ? -comparison : comparison
    })

    return sorted
  }, [projects, sortDescending, sortKey])

  const currentStep: Step = selectedStep

  const openTemplateEditor = () => {
    if (!activeProjectId) return
    setActiveNav('templates')
    setTemplateOpen(true)
  }

  const handleCreateProject = async () => {
    const name = window.prompt('Project name:')
    if (!name?.trim()) return

    try {
      const project = await createProject(name.trim())
      setActiveProjectId(project.id)
      setActiveNav('reports')
    } catch (error) {
      console.error(error)
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    const project = projects.find((item) => item.id === projectId)
    if (!project) return
    const confirmed = window.confirm(`Delete ${project.name}? This cannot be undone.`)
    if (!confirmed) return

    try {
      await deleteProject(projectId)
      if (activeProjectId === projectId) {
        setActiveProjectId(projects.find((item) => item.id !== projectId)?.id ?? null)
      }
      await refreshProjects()
    } catch (error) {
      console.error(error)
    }
  }

  const handleUploadFiles = async (files: File[]) => {
    await uploadFiles(files)
  }

  const handleGenerateReport = async () => {
    const detail = await createReport()
    if (detail) {
      setSelectedStep(3)
      setSelectedCitationId(detail.citations[0]?.citation_id ?? null)
      if (activeProjectId) {
        reportStepInitRef.current = activeProjectId
      }
    }
  }

  const activeReport = report
  const citationLookupId = selectedCitationId ?? activeReport?.citations[0]?.citation_id ?? null
  const { citationLookup, loading: citationLoading } = useCitation(
    activeReport?.id ?? null,
    citationLookupId,
  )

  useEffect(() => {
    if (activeReport?.citations.length) {
      setSelectedCitationId((current) => current ?? activeReport.citations[0].citation_id)
    }
  }, [activeReport])

  const reportText = activeReport?.report_text ?? ''
  const citations = activeReport?.citations ?? []
  const selectedCitation = citationLookup?.citation ?? citations.find((citation) => citation.citation_id === citationLookupId) ?? null
  const evidenceChunks = citationLookup?.chunks ?? []

  const renderMainContent = () => {
    if (activeNav === 'templates') {
      return (
        <div className="flex h-full items-center justify-center p-8">
          <div className="w-full max-w-2xl rounded-[2rem] border border-black/[0.12] bg-black/[0.04] p-8 shadow-[0_20px_80px_rgba(0,0,0,0.08)]">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-black/[0.06] text-[color:var(--text-primary)]">
                <SquarePen className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold text-[color:var(--text-primary)]">
                  Template workflow
                </div>
                <div className="text-sm text-[color:var(--text-secondary)]">
                  Edit, customise, and manage your report templates.
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-3 text-sm leading-relaxed text-[color:var(--text-secondary)]">
              <p>
                Use the report workflow for uploads, quality review, and report generation. When
                you need to edit the template for the selected project, open the editor from this
                view.
              </p>
              {!activeProjectId ? (
                <p>Select a project in Reports first, then return here.</p>
              ) : null}
            </div>

            <div className="mt-6 flex gap-3">
              <Button type="button" onClick={openTemplateEditor} disabled={!activeProjectId}>
                Open Template Editor
              </Button>
              <Button type="button" variant="outline" onClick={() => setActiveNav('reports')}>
                Back to Reports
              </Button>
            </div>
          </div>
        </div>
      )
    }

    if (activeNav === 'data diagnostics') {
      return (
        <div className="flex h-full items-center justify-center p-8">
          <EmptyState
            title="Data Diagnostics placeholder"
            description="Data diagnostics functionality is reserved for future implementation."
          />
        </div>
      )
    }

    if (!activeProjectId) {
      return (
        <div className="flex h-full items-center justify-center p-8">
          <EmptyState
            title="No project selected"
            description="Create a report project to start the upload and review flow."
            action={
              <Button type="button" onClick={handleCreateProject}>
                Create project
              </Button>
            }
          />
        </div>
      )
    }

    if (currentStep === 1) {
      return (
      <StepOneUpload
          activeProjectId={activeProjectId}
          documents={documents}
          uploading={uploading}
          allReady={allReady}
          onUploadFiles={handleUploadFiles}
          onRetryUpload={retryUpload}
          onContinue={() => setSelectedStep(2)}
          currentStep={currentStep}
          onStepChange={setSelectedStep}
        />
      )
    }

    if (currentStep === 2) {
      return (
        <StepTwoReview
          criteriaChecked={criteriaChecked}
          passed={passed}
          needsReview={needsReview}
          groupedFlags={groupedFlags}
          onResolveFlag={resolveFlag}
          onBack={() => setSelectedStep(1)}
          onGenerateReport={handleGenerateReport}
          generating={generating}
          currentStep={currentStep}
          onStepChange={setSelectedStep}
        />
      )
    }

    return (
      <StepThreeReport
        projectId={activeProjectId}
        report={activeReport}
        reportText={reportText}
        citations={citations}
        selectedCitationId={citationLookupId}
        selectedCitation={selectedCitation}
        evidenceChunks={evidenceChunks}
        evidenceLoading={citationLoading}
        onSelectCitation={setSelectedCitationId}
        onBack={() => setSelectedStep(2)}
        onDownload={downloadCurrentReport}
        onSend={sendMessage}
        messages={messages}
        isStreaming={isStreaming}
        activeToolCall={activeToolCall}
        currentStep={currentStep}
        onStepChange={setSelectedStep}
      />
    )
  }

  return (
    <TooltipProvider>
      <div className="flex h-screen w-full overflow-hidden bg-[#FFFCF5] text-[color:var(--text-primary)]">
        <aside
          className="relative flex h-full flex-col border-r border-black/10 bg-[#FFFCF5] backdrop-blur-xl transition-[width] duration-200"
          style={{ width: sidebarExpanded ? 140 : 52 }}
          onMouseEnter={() => setSidebarHovered(true)}
          onMouseLeave={() => setSidebarHovered(false)}
        >
          <div className="flex items-center justify-center border-b border-black/10 p-2">
            <button
              type="button"
              onClick={() => setSidebarPinned((value) => !value)}
              className="flex h-8 w-8 items-center justify-center rounded-xl bg-black/[0.05] text-[color:var(--text-secondary)] transition hover:bg-black/[0.09] hover:text-[color:var(--text-primary)]"
              aria-label={sidebarPinned ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              <ArrowDownWideNarrow className={`h-4 w-4 transition-transform ${sidebarPinned ? 'rotate-90' : ''}`} />
            </button>
          </div>

          <div className="flex flex-1 flex-col gap-2 p-2">
            {NAV_ITEMS.map((item) => (
              <SidebarNavButton
                key={item.id}
                label={item.label}
                icon={item.icon}
                active={activeNav === item.id}
                disabled={item.disabled}
                expanded={sidebarExpanded}
                onClick={() => {
                  if (item.disabled) return
                  setActiveNav(item.id)
                  if (item.id === 'templates') {
                    openTemplateEditor()
                  }
                }}
                tooltip={item.tooltip}
              />
            ))}
          </div>

          <div className="border-t border-black/10 p-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={() => {
                    setSidebarPinned((value) => !value)
                  }}
                  className="flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-sm text-[color:var(--text-secondary)] transition hover:bg-black/[0.05] hover:text-[color:var(--text-primary)]"
                >
                  <ArrowDownAZ className="h-4 w-4 shrink-0" />
                  {sidebarExpanded ? <span>Settings</span> : null}
                </button>
              </TooltipTrigger>
              <TooltipContent>{sidebarPinned ? 'Collapse' : 'Expand'}</TooltipContent>
            </Tooltip>
          </div>
        </aside>

        {activeNav === 'reports' ? (
          <section className="flex h-full w-[340px] shrink-0 min-w-0 flex-col border-r border-black/10 bg-black/[0.02]">
            <div className="border-b border-black/10 px-5 py-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
                    Projects
                  </div>
                  <div className="mt-1 text-sm text-[color:var(--text-secondary)]">
                    Reports dashboard
                  </div>
                </div>
                <Button type="button" size="xs" onClick={handleCreateProject}>
                  <Plus className="h-3.5 w-3.5" />
                  New
                </Button>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {(['created_at', 'name', 'status'] as const).map((key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => {
                      if (sortKey === key) {
                        setSortDescending((value) => !value)
                      } else {
                        setSortKey(key)
                        setSortDescending(key === 'created_at')
                      }
                    }}
                    className={[
                      'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] uppercase tracking-[0.28em] transition',
                      sortKey === key
                        ? 'border-black/[0.15] bg-black/[0.1] text-[color:var(--text-primary)]'
                        : 'border-black/[0.12] bg-black/[0.03] text-[color:var(--text-secondary)] hover:bg-black/[0.07]',
                    ].join(' ')}
                  >
                    {key}
                    {sortKey === key ? (
                      <span>{sortDescending ? 'desc' : 'asc'}</span>
                    ) : null}
                  </button>
                ))}
              </div>
            </div>

            <ScrollArea className="min-h-0 flex-1">
              <div className="space-y-3 p-4">
                {projectsLoading ? (
                  <div className="rounded-2xl border border-black/10 bg-black/[0.03] p-4 text-sm text-[color:var(--text-secondary)]">
                    Loading projects...
                  </div>
                ) : displayedProjects.length === 0 ? (
                  <EmptyState
                    title="No projects yet"
                    description="Create a project to begin the review workflow."
                    action={
                      <Button type="button" onClick={handleCreateProject}>
                        Create project
                      </Button>
                    }
                  />
                ) : (
                  displayedProjects.map((project) => (
                    <ProjectRow
                      key={project.id}
                      project={project}
                      active={project.id === activeProjectId}
                      onSelect={() => {
                        setActiveProjectId(project.id)
                        setActiveNav('reports')
                      }}
                      onDelete={() => handleDeleteProject(project.id)}
                    />
                  ))
                )}
              </div>
            </ScrollArea>
          </section>
        ) : null}

        <main className="min-w-0 flex-1 overflow-hidden">{renderMainContent()}</main>
      </div>

      <TemplateEditor projectId={activeProjectId} open={templateOpen} onOpenChange={setTemplateOpen} />
    </TooltipProvider>
  )
}

function StepShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string
  subtitle: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-black/10 px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-[10px] uppercase tracking-[0.35em] text-[color:var(--text-secondary)]">
              {title}
            </div>
            <div className="mt-2 text-sm leading-relaxed text-[color:var(--text-secondary)]">
              {subtitle}
            </div>
          </div>
          {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
    </div>
  )
}

function StepHeader({
  currentStep,
  onStepChange,
  step2Unlocked,
  step3Unlocked,
}: {
  currentStep: Step
  onStepChange: (step: Step) => void
  step2Unlocked: boolean
  step3Unlocked: boolean
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-3xl border border-black/[0.12] bg-black/[0.04] p-2">
      {([1, 2, 3] as Step[]).map((step) => {
        const unlocked =
          step === 1 || (step === 2 && step2Unlocked) || (step === 3 && step3Unlocked)
        const active = currentStep === step

        return (
          <button
            key={step}
            type="button"
            disabled={!unlocked}
            onClick={() => onStepChange(step)}
            className={[
              'inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm transition',
              active
                ? 'bg-[color:var(--accent)] text-white'
                : unlocked
                  ? 'bg-black/[0.04] text-[color:var(--text-secondary)] hover:bg-black/[0.08] hover:text-[color:var(--text-primary)]'
                  : 'cursor-not-allowed bg-black/[0.03] text-[color:var(--text-secondary)] opacity-40',
            ].join(' ')}
          >
            <span className="text-[10px] uppercase tracking-[0.3em]">{step}</span>
            <span>{STEP_LABELS[step]}</span>
          </button>
        )
      })}
    </div>
  )
}

function StepOneUpload({
  activeProjectId,
  documents,
  uploading,
  allReady,
  onUploadFiles,
  onRetryUpload,
  onContinue,
  currentStep,
  onStepChange,
}: {
  activeProjectId: string
  documents: Array<{
    id: string
    filename: string
    status: 'uploading' | 'chunking' | 'embedded' | 'ready' | 'error'
    sourceFile?: File
  }>
  uploading: boolean
  allReady: boolean
  onUploadFiles: (files: File[]) => Promise<void>
  onRetryUpload: (documentId: string) => Promise<void>
  onContinue: () => void
  currentStep: Step
  onStepChange: (step: Step) => void
}) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList?.length) return
    await onUploadFiles(Array.from(fileList))
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <StepShell
      title="Step 1"
      subtitle="Upload source documents. Each file is polled until it reaches ready status."
      actions={
        <StepHeader
          currentStep={currentStep}
          onStepChange={onStepChange}
          step2Unlocked={allReady && documents.length > 0}
          step3Unlocked={false}
        />
      }
    >
      <div className="grid h-full min-h-0 gap-4 p-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="min-h-0 rounded-[2rem] border border-black/[0.12] bg-black/[0.04] p-4">
          <div
            className={[
              'flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-[1.75rem] border border-dashed p-6 text-center transition',
              dragOver ? 'border-[color:var(--accent)] bg-emerald-500/5' : 'border-black/[0.12] bg-black/[0.03]',
            ].join(' ')}
            onDragOver={(event) => {
              event.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={async (event) => {
              event.preventDefault()
              setDragOver(false)
              await handleUpload(event.dataTransfer.files)
            }}
            onClick={() => inputRef.current?.click()}
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-black/[0.07] text-[color:var(--accent)]">
              <Upload className="h-6 w-6" />
            </div>
            <div className="mt-4 text-lg font-semibold text-[color:var(--text-primary)]">
              Drop files here or click to browse
            </div>
            <div className="mt-2 max-w-lg text-sm leading-relaxed text-[color:var(--text-secondary)]">
              The backend will process each upload through chunking, embedding, and ready status
              polling.
            </div>
            <div className="mt-4 flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
              <span>{activeProjectId}</span>
              <span>·</span>
              <span>{uploading ? 'Uploading' : 'Idle'}</span>
            </div>
            <input
              ref={inputRef}
              type="file"
              multiple
              className="hidden"
              onChange={async (event) => {
                await handleUpload(event.target.files)
              }}
            />
          </div>

          <div className="mt-4 flex items-center justify-between gap-3">
            <div className="text-xs uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
              Uploaded files
            </div>
            <Button type="button" variant="outline" size="xs" onClick={() => inputRef.current?.click()}>
              Browse files
            </Button>
          </div>

          <div className="mt-3 space-y-3">
            {documents.length === 0 ? (
              <EmptyState
                title="No uploads yet"
                description="Add the source files for this project to unlock the quality review step."
              />
            ) : (
              documents.map((document) => {
                const busy = ['uploading', 'chunking', 'embedded'].includes(document.status)
                return (
                  <div
                    key={document.id}
                    className="flex items-start justify-between gap-3 rounded-2xl border border-black/10 bg-black/[0.04] px-4 py-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-[color:var(--text-primary)]">
                        {document.filename}
                      </div>
                      <div className="mt-1 flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-2 rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.28em] ${statusPillClass(document.status)}`}
                        >
                          {DOCUMENT_STATUS_LABELS[document.status]}
                          {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                        </span>
                        {busy ? (
                          <span className="text-xs text-[color:var(--text-secondary)]">
                            Processing in the background
                          </span>
                        ) : null}
                      </div>
                    </div>
                    {document.status === 'error' && document.sourceFile ? (
                      <Button type="button" variant="outline" size="xs" onClick={() => onRetryUpload(document.id)}>
                        Retry
                      </Button>
                    ) : null}
                  </div>
                )
              })
            )}
          </div>
        </div>

        <div className="flex min-h-0 flex-col gap-4 rounded-[2rem] border border-black/[0.12] bg-black/[0.04] p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <MetricCard
              label="Files"
              value={documents.length}
              detail="Uploaded documents in the current project."
            />
            <MetricCard
              label="Ready"
              value={documents.filter((document) => document.status === 'ready').length}
              detail="Only ready files unlock the next step."
            />
          </div>

          <div className="rounded-3xl border border-black/10 bg-black/[0.06] p-4">
            <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
              Continue
            </div>
            <div className="mt-2 text-sm text-[color:var(--text-secondary)]">
              {allReady
                ? 'All documents are ready. Move into the data quality review.'
                : 'Continue remains disabled until every upload reaches ready status.'}
            </div>
            <div className="mt-4">
              <Button type="button" disabled={!allReady || documents.length === 0} onClick={onContinue}>
                Continue to review
              </Button>
            </div>
          </div>
        </div>
      </div>
    </StepShell>
  )
}

function StepTwoReview({
  criteriaChecked,
  passed,
  needsReview,
  groupedFlags,
  onResolveFlag,
  onBack,
  onGenerateReport,
  generating,
  currentStep,
  onStepChange,
}: {
  criteriaChecked: number
  passed: number
  needsReview: number
  groupedFlags: Record<'gap' | 'conflict' | 'missing', GapFlag[]>
  onResolveFlag: (id: string) => void
  onBack: () => void
  onGenerateReport: () => Promise<void>
  generating: boolean
  currentStep: Step
  onStepChange: (step: Step) => void
}) {
  return (
    <StepShell
      title="Step 2"
      subtitle="Review schema coverage and unresolved quality flags before generating the final report."
      actions={
        <StepHeader
          currentStep={currentStep}
          onStepChange={onStepChange}
          step2Unlocked
          step3Unlocked={false}
        />
      }
    >
      <div className="flex h-full min-h-0 flex-col gap-4 p-4">
        <div className="grid gap-3 lg:grid-cols-3">
          <MetricCard
            label="Criteria checked"
            value={criteriaChecked}
            detail="Required schema fields returned by the backend."
          />
          <MetricCard
            label="Passed"
            value={passed}
            detail="Coverage without unresolved review flags."
          />
          <MetricCard
            label="Needs review"
            value={needsReview}
            detail="Unresolved gaps, conflicts, and missing fields."
          />
        </div>

        <div className="min-h-0 flex-1 overflow-hidden rounded-[2rem] border border-black/[0.12] bg-black/[0.04] p-4">
          <div className="flex items-center justify-between gap-3 border-b border-black/10 pb-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
                Review flags
              </div>
              <div className="mt-1 text-sm text-[color:var(--text-secondary)]">
                Flags are grouped by type, matching the current backend model.
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-2xl border border-black/[0.12] bg-black/[0.03] px-3 py-2 text-sm text-[color:var(--text-secondary)] transition hover:bg-black/[0.07] hover:text-[color:var(--text-primary)]"
              >
                <Funnel className="h-4 w-4" />
                Filters
              </button>
              <Button type="button" variant="outline" size="xs" onClick={onBack}>
                Back
              </Button>
            </div>
          </div>

          <ScrollArea className="mt-4 h-[calc(100%-3rem)]">
            <div className="space-y-4 pr-2">
              {(['gap', 'conflict', 'missing'] as const).map((flagType) => (
                <details key={flagType} open className="rounded-[1.5rem] border border-black/10 bg-black/[0.05]">
                  <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold uppercase tracking-[0.28em] text-[color:var(--text-primary)]">
                    {flagType}
                  </summary>
                  <div className="space-y-3 px-4 pb-4">
                    {groupedFlags[flagType].length === 0 ? (
                      <div className="rounded-2xl border border-dashed border-black/10 bg-black/[0.03] p-4 text-sm text-[color:var(--text-secondary)]">
                        No {flagType} flags.
                      </div>
                    ) : (
                      groupedFlags[flagType].map((flag) => (
                        <FlagRow key={flag.id} flag={flag} onResolve={onResolveFlag} />
                      ))
                    )}
                  </div>
                </details>
              ))}
            </div>
          </ScrollArea>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[2rem] border border-black/[0.12] bg-black/[0.04] px-4 py-4">
          <div className="text-sm text-[color:var(--text-secondary)]">
            Generate the report after resolving the items you care about. The report is written to a
            Markdown artifact and recorded as an analysis output.
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onBack}>
              Back to uploads
            </Button>
            <Button type="button" onClick={onGenerateReport} disabled={generating}>
              {generating ? 'Generating…' : 'Generate report'}
            </Button>
          </div>
        </div>
      </div>
    </StepShell>
  )
}

function StepThreeReport({
  projectId,
  report,
  reportText,
  citations,
  selectedCitationId,
  selectedCitation,
  evidenceChunks,
  evidenceLoading,
  onSelectCitation,
  onBack,
  onDownload,
  onSend,
  messages,
  isStreaming,
  activeToolCall,
  currentStep,
  onStepChange,
}: {
  projectId: string
  report: ReportDetail | null
  reportText: string
  citations: ReportCitation[]
  selectedCitationId: string | null
  selectedCitation: ReportCitation | null
  evidenceChunks: EvidenceChunk[]
  evidenceLoading: boolean
  onSelectCitation: (citationId: string | null) => void
  onBack: () => void
  onDownload: () => Promise<void>
  onSend: (message: string) => void
  messages: Parameters<typeof MessageList>[0]['messages']
  isStreaming: boolean
  activeToolCall: Parameters<typeof MessageList>[0]['activeToolCall']
  currentStep: Step
  onStepChange: (step: Step) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="border-b border-black/10 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <StepHeader
            currentStep={currentStep}
            onStepChange={onStepChange}
            step2Unlocked
            step3Unlocked
          />
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={onBack}>
              Back to review
            </Button>
            <Button type="button" variant="outline" onClick={onDownload} disabled={!report}>
              Download
            </Button>
          </div>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 gap-0 xl:grid-cols-[minmax(0,1.35fr)_420px]">
        <div className="min-h-0 border-r border-black/10">
          <div className="flex h-full min-h-0 flex-col overflow-hidden">
            <div className="border-b border-black/10 px-6 py-4">
              <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
                Report preview
              </div>              
              {citations.length ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {citations.map((citation) => (
                    <button
                      key={citation.citation_id}
                      type="button"
                      onClick={() => onSelectCitation(citation.citation_id)}
                      className={[
                        'rounded-full border px-3 py-1.5 text-[10px] uppercase tracking-[0.28em] transition',
                        selectedCitationId === citation.citation_id
                          ? 'border-[color:var(--accent)] bg-emerald-500/10 text-[color:var(--text-primary)]'
                          : 'border-black/[0.12] bg-black/[0.03] text-[color:var(--text-secondary)] hover:bg-black/[0.07]',
                      ].join(' ')}
                    >
                      {citation.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            <ScrollArea className="min-h-0 flex-1">
              <div className="px-6 py-5">
                {reportText ? (
                  <div className="rounded-[1rem] border border-black/10 bg-black/[0.06] p-5">
                    <MarkdownRenderer content={reportText} />
                  </div>
                ) : (
                  <EmptyState
                    title="Report not loaded yet"
                    description="Generate a report or wait for the latest analysis output to finish loading."
                  />
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        <div className="flex min-h-0 flex-col bg-black/[0.03]">
          <div className="min-h-0 flex-1 border-b border-black/10">
            <div className="flex h-full min-h-0 flex-col overflow-hidden">
              <div className="border-b border-black/10 px-5 py-4">
                <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
                  Evidence
                </div>
                <div className="mt-1 text-sm text-[color:var(--text-secondary)]">
                  Click a citation to inspect matching evidence chunks.
                </div>
                {selectedCitation ? (
                  <div className="mt-3 text-xs text-[color:var(--text-secondary)]">
                    Selected: {selectedCitation.label} · {selectedCitation.filename} · chunk{' '}
                    {selectedCitation.chunk_index}
                  </div>
                ) : null}
              </div>

              <ScrollArea className="min-h-0 flex-1">
                <div className="space-y-3 p-4">
                  {!selectedCitation ? (
                    <EmptyState
                      title="No citation selected"
                      description={
                        citations.length
                          ? 'Select a citation above to load the linked evidence.'
                          : 'This report does not expose citation metadata yet.'
                      }
                    />
                  ) : evidenceLoading ? (
                    <div className="rounded-2xl border border-black/10 bg-black/[0.04] p-4 text-sm text-[color:var(--text-secondary)]">
                      Loading evidence...
                    </div>
                  ) : evidenceChunks.length === 0 ? (
                    <EmptyState
                      title="No matching evidence"
                      description="The report references this citation, but the backend did not return matching chunks."
                    />
                  ) : (
                    evidenceChunks.map((chunk) => (
                      <div
                        key={chunk.id}
                        className="rounded-2xl border border-black/10 bg-black/[0.04] p-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-[color:var(--text-primary)]">
                            {chunk.filename}
                          </div>
                          <Badge className={`rounded-full px-2 py-1 ${statusPillClass('ready')}`}>
                            Chunk {chunk.chunk_index}
                          </Badge>
                        </div>
                        <div className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-[color:var(--text-secondary)]">
                          {chunk.content}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>

          <div className="min-h-0 flex-[1.15]">
            <div className="flex h-full min-h-0 flex-col overflow-hidden">
              <div className="border-b border-black/10 px-5 py-2">
                <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--text-secondary)]">
                  Chat
                </div>
              </div>
              <MessageList messages={messages} activeToolCall={activeToolCall} isStreaming={isStreaming} />
              <ChatInput onSend={onSend} disabled={isStreaming || !projectId} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function WorkspacePage() {
  return <WorkspacePageBody />
}
