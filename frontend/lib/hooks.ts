'use client'

import { useState, useCallback, useEffect } from 'react'
import { fetchProcessingReport, uploadDocument } from './api'
import type { ProcessingReport } from './types'

export function useDocumentUpload() {
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true)
    setProgress(0)
    setError(null)
    setDocumentId(null)

    try {
      const response = await uploadDocument(file)
      setDocumentId(response.id)
      setProgress(100)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsUploading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setIsUploading(false)
    setProgress(0)
    setError(null)
    setDocumentId(null)
  }, [])

  return {
    uploadFile,
    isUploading,
    progress,
    error,
    documentId,
    reset,
  }
}

export function useDocumentReport(documentId: string | null) {
  const [report, setReport] = useState<ProcessingReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReport = useCallback(async () => {
    if (!documentId) return

    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchProcessingReport(documentId)
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    if (documentId) {
      fetchReport()
    }
  }, [documentId, fetchReport])

  return {
    report,
    isLoading,
    error,
    isProcessing: false,
    refetch: fetchReport,
  }
}

export function usePagination(items: any[], itemsPerPage: number = 1) {
  const [currentPage, setCurrentPage] = useState(1)

  const totalPages = Math.ceil(items.length / itemsPerPage)
  const startIdx = (currentPage - 1) * itemsPerPage
  const endIdx = startIdx + itemsPerPage
  const currentItems = items.slice(startIdx, endIdx)

  const goToPage = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)))
  }, [totalPages])

  const nextPage = useCallback(() => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
  }, [totalPages])

  const prevPage = useCallback(() => {
    setCurrentPage((prev) => Math.max(prev - 1, 1))
  }, [])

  return {
    currentPage,
    totalPages,
    currentItems,
    goToPage,
    nextPage,
    prevPage,
  }
}
