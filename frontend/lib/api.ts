import type { ProcessingReport, UploadResponse } from './types'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    return data.detail || data.error || 'Request failed'
  } catch {
    return 'Request failed'
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json()
}

export async function fetchProcessingReport(
  documentId: string
): Promise<ProcessingReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/${documentId}/processing-report`
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json()
}
