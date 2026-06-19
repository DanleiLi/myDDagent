import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '@/lib/api'

const REPORT_SCRIPT_NAME = 'generate_final_report'

export function useReport(projectId: string | null) {
  const [outputs, setOutputs] = useState<api.AnalysisOutput[]>([])
  const [currentReportId, setCurrentReportId] = useState<string | null>(null)
  const [report, setReport] = useState<api.ReportDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    setOutputs([])
    setCurrentReportId(null)
    setReport(null)
  }, [projectId])

  const refresh = useCallback(async () => {
    if (!projectId) {
      setOutputs([])
      setCurrentReportId(null)
      setReport(null)
      return
    }

    setLoading(true)
    try {
      const currentOutputs = await api.listAnalysisOutputs(projectId)
      const reportOutputs = currentOutputs.filter(
        (output) => output.script_name === REPORT_SCRIPT_NAME,
      )
      setOutputs(reportOutputs)
      setCurrentReportId((prev) => {
        if (prev && reportOutputs.some((output) => output.id === prev)) {
          return prev
        }
        return reportOutputs[0]?.id ?? null
      })
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void refresh()

    if (!projectId) return

    const interval = setInterval(() => {
      void refresh()
    }, 5000)

    return () => clearInterval(interval)
  }, [projectId, refresh])

  useEffect(() => {
    if (!currentReportId) {
      setReport(null)
      return
    }

    let cancelled = false
    const loadReport = async () => {
      try {
        const detail = await api.getReport(currentReportId)
        if (!cancelled) setReport(detail)
      } catch (error) {
        console.error(error)
        if (!cancelled) setReport(null)
      }
    }

    void loadReport()

    return () => {
      cancelled = true
    }
  }, [currentReportId])

  const selectReport = useCallback((reportId: string) => {
    setCurrentReportId(reportId)
  }, [])

  const createReport = useCallback(async () => {
    if (!projectId) return null
    setGenerating(true)
    try {
      const detail = await api.createReport(projectId)
      setOutputs((prev) => {
        const next = prev.filter((output) => output.id !== detail.id)
        return [detail, ...next]
      })
      setCurrentReportId(detail.id)
      setReport(detail)
      return detail
    } finally {
      setGenerating(false)
    }
  }, [projectId])

  const currentOutput = useMemo(
    () => outputs.find((output) => output.id === currentReportId) ?? outputs[0] ?? null,
    [currentReportId, outputs],
  )

  const hasReport = outputs.length > 0

  const downloadCurrentReport = useCallback(async () => {
    if (!currentOutput) return
    await api.downloadAnalysisOutput(currentOutput.id)
  }, [currentOutput])

  return {
    outputs,
    currentOutput,
    report,
    loading,
    generating,
    hasReport,
    refresh,
    selectReport,
    createReport,
    downloadCurrentReport,
  }
}
