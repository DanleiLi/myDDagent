import { useEffect, useState } from 'react'
import * as api from '@/lib/api'

export function useAnalysisOutputs(projectId: string | null) {
  const [outputs, setOutputs] = useState<api.AnalysisOutput[]>([])

  useEffect(() => {
    let cancelled = false

    const refresh = async () => {
      if (!projectId) {
        if (!cancelled) setOutputs([])
        return
      }

      try {
        const currentOutputs = await api.listAnalysisOutputs(projectId)
        if (!cancelled) setOutputs(currentOutputs)
      } catch (error) {
        console.error(error)
      }
    }

    void refresh()

    if (!projectId) {
      return () => {
        cancelled = true
      }
    }

    const interval = setInterval(() => {
      void refresh()
    }, 5000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [projectId])

  return { outputs }
}
