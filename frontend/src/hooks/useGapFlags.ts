import { useCallback, useEffect, useState } from 'react'
import * as api from '@/lib/api'
import { supabase } from '@/lib/supabase'

export function useGapFlags(projectId: string | null) {
  const [flags, setFlags] = useState<api.GapFlag[]>([])
  const unresolvedCount = flags.filter((flag) => !flag.resolved).length

  const refresh = useCallback(async () => {
    if (!projectId) {
      setFlags([])
      return
    }
    try {
      const currentFlags = await api.listGapFlags(projectId)
      setFlags(currentFlags)
    } catch (error) {
      console.error(error)
    }
  }, [projectId])

  useEffect(() => {
    void refresh()

    if (!projectId) {
      return
    }

    const interval = setInterval(() => {
      void refresh()
    }, 5000)

    const channel = supabase
      .channel(`gap-flags-${projectId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'gap_flags',
          filter: `project_id=eq.${projectId}`,
        },
        () => {
          void refresh()
        },
      )
      .subscribe()

    return () => {
      clearInterval(interval)
      void supabase.removeChannel(channel)
    }
  }, [refresh])

  const resolveFlag = useCallback(async (gapId: string) => {
    // Optimistic update
    setFlags((prev) => prev.map((f) => (f.id === gapId ? { ...f, resolved: true } : f)))
    try {
      await api.resolveGapFlag(gapId)
    } catch {
      // Revert on failure
      setFlags((prev) => prev.map((f) => (f.id === gapId ? { ...f, resolved: false } : f)))
    }
  }, [])

  return { flags, unresolvedCount, resolveFlag, refresh }
}
