import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as api from '@/lib/api'

export interface TrackedDocument extends api.Document {
  sourceFile?: File
}

const TERMINAL_STATUSES: api.Document['status'][] = ['ready', 'error']

export function useDocuments(projectId: string | null) {
  const [documents, setDocuments] = useState<TrackedDocument[]>([])
  const [uploading, setUploading] = useState(false)
  const pollingRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map())
  const fileMapRef = useRef<Map<string, File>>(new Map())

  const stopPolling = useCallback((documentId: string) => {
    const existing = pollingRef.current.get(documentId)
    if (existing) {
      clearInterval(existing)
      pollingRef.current.delete(documentId)
    }
  }, [])

  function startPolling(documentId: string) {
    if (pollingRef.current.has(documentId)) return

    const interval = setInterval(async () => {
      try {
        const result = await api.getDocumentStatus(documentId)
        setDocuments((prev) =>
          prev.map((document) =>
            document.id === documentId
              ? { ...document, status: result.status, sourceFile: fileMapRef.current.get(documentId) }
              : document,
          ),
        )

        if (TERMINAL_STATUSES.includes(result.status)) {
          stopPolling(documentId)
        }
      } catch (error) {
        console.error(error)
        stopPolling(documentId)
      }
    }, 2000)

    pollingRef.current.set(documentId, interval)
  }

  const syncRemoteDocuments = useCallback(
    (remoteDocuments: api.Document[]) => {
      setDocuments(
        remoteDocuments.map((document) => ({
          ...document,
          sourceFile: fileMapRef.current.get(document.id),
        })),
      )

      for (const document of remoteDocuments) {
        if (TERMINAL_STATUSES.includes(document.status)) {
          stopPolling(document.id)
          continue
        }
        startPolling(document.id)
      }
    },
    [stopPolling],
  )

  const refresh = useCallback(async () => {
    if (!projectId) {
      setDocuments([])
      return
    }

    try {
      const remoteDocuments = await api.listDocuments(projectId)
      syncRemoteDocuments(remoteDocuments)
    } catch (error) {
      console.error(error)
    }
  }, [projectId, syncRemoteDocuments])

  useEffect(() => {
    void refresh()

    return () => {
      pollingRef.current.forEach((interval) => clearInterval(interval))
      pollingRef.current.clear()
    }
  }, [refresh])

  const uploadFile = useCallback(
    async (file: File, replaceDocumentId?: string) => {
      if (!projectId) return null

      const doc = await api.uploadDocument(projectId, file)
      fileMapRef.current.set(doc.id, file)

      setDocuments((prev) => {
        const next = replaceDocumentId ? prev.filter((item) => item.id !== replaceDocumentId) : prev
        return [{ ...doc, sourceFile: file }, ...next]
      })

      if (!TERMINAL_STATUSES.includes(doc.status)) {
        startPolling(doc.id)
      }

      return doc
    },
    [projectId, startPolling],
  )

  const uploadFiles = useCallback(
    async (files: File[]) => {
      if (!files.length || !projectId) return
      setUploading(true)
      try {
        for (const file of files) {
          await uploadFile(file)
        }
      } finally {
        setUploading(false)
      }
    },
    [projectId, uploadFile],
  )

  const retryUpload = useCallback(
    async (documentId: string) => {
      const sourceFile = fileMapRef.current.get(documentId)
      if (!sourceFile || !projectId) return
      await uploadFile(sourceFile, documentId)
    },
    [projectId, uploadFile],
  )

  const allReady = useMemo(
    () => documents.length > 0 && documents.every((document) => document.status === 'ready'),
    [documents],
  )

  const hasError = useMemo(
    () => documents.some((document) => document.status === 'error'),
    [documents],
  )

  return {
    documents,
    uploading,
    allReady,
    hasError,
    uploadDocument: async (file: File) => {
      await uploadFile(file)
    },
    uploadFile,
    uploadFiles,
    retryUpload,
    refresh,
  }
}
