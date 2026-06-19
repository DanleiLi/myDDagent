import { useEffect, useState } from 'react'
import * as api from '@/lib/api'

export function useCitation(reportId: string | null, citationId: string | null) {
  const [citationLookup, setCitationLookup] = useState<api.ReportCitationLookup | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!reportId || !citationId) {
      setCitationLookup(null)
      setLoading(false)
      return
    }

    let cancelled = false
    const loadCitation = async () => {
      setLoading(true)
      try {
        const nextCitation = await api.getReportCitation(reportId, citationId)
        if (!cancelled) setCitationLookup(nextCitation)
      } catch (error) {
        console.error(error)
        if (!cancelled) setCitationLookup(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadCitation()

    return () => {
      cancelled = true
    }
  }, [reportId, citationId])

  return { citationLookup, loading }
}
