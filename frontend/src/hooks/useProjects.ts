import { useCallback, useEffect, useState } from 'react'
import * as api from '@/lib/api'

export function useProjects() {
  const [projects, setProjects] = useState<api.Project[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const currentProjects = await api.listProjects()
      setProjects(currentProjects)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const createProject = useCallback(async (name: string): Promise<api.Project> => {
    const project = await api.createProject(name)
    setProjects((prev) => [project, ...prev])
    return project
  }, [])

  const deleteProject = useCallback(async (id: string) => {
    await api.deleteProject(id)
    setProjects((prev) => prev.filter((project) => project.id !== id))
  }, [])

  return { projects, createProject, deleteProject, loading, refresh }
}
