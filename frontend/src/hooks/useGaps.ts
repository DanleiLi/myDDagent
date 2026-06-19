import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '@/lib/api'

export function useGaps(projectId: string | null) {
  const [flags, setFlags] = useState<api.GapFlag[]>([])
  const [schema, setSchema] = useState<api.DDSchema | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!projectId) {
      setFlags([])
      setSchema(null)
      return
    }

    setLoading(true)
    try {
      const [nextSchema, nextFlags] = await Promise.all([
        api.getSchema(projectId).catch(() => null),
        api.listGapFlags(projectId).catch(() => [] as api.GapFlag[]),
      ])
      setSchema(nextSchema)
      setFlags(nextFlags)
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

  const resolveFlag = useCallback(async (gapId: string) => {
    setFlags((prev) => prev.map((flag) => (flag.id === gapId ? { ...flag, resolved: true } : flag)))
    try {
      await api.resolveGapFlag(gapId)
    } catch (error) {
      console.error(error)
      setFlags((prev) => prev.map((flag) => (flag.id === gapId ? { ...flag, resolved: false } : flag)))
    }
  }, [])

  const unresolvedFlags = useMemo(() => flags.filter((flag) => !flag.resolved), [flags])

  const criteriaChecked = useMemo(
    () => schema?.fields.filter((field) => field.required !== false).length ?? 0,
    [schema],
  )

  const needsReview = unresolvedFlags.length
  const passed = Math.max(criteriaChecked - needsReview, 0)

  const groupedFlags = useMemo(() => {
    const groups: Record<api.GapFlag['flag_type'], api.GapFlag[]> = {
      gap: [],
      conflict: [],
      missing: [],
    }

    for (const flag of flags) {
      groups[flag.flag_type].push(flag)
    }

    return groups
  }, [flags])

  return {
    flags,
    groupedFlags,
    schema,
    loading,
    criteriaChecked,
    passed,
    needsReview,
    unresolvedFlags,
    resolveFlag,
    refresh,
  }
}
