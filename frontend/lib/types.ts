export interface PageResult {
  page_number: number
  document_type: string | null
  classification_confidence: number | null
  ocr_text_length: number
  segmentation_object_count: number
  extraction_json: ExtractionJson | null
}

export interface ExtractionField {
  name?: string
  field_name?: string
  value?: unknown
  [key: string]: unknown
}

export interface ExtractionJson {
  document_type?: string
  classification_confidence?: number
  extraction_confidence?: number
  raw_ocr_text?: string
  fields?: ExtractionField[]
  metadata?: {
    ocr_confidence?: number
    [key: string]: unknown
  }
  [key: string]: unknown
}

export interface ProcessingReport {
  document_id: string
  original_filename: string
  page_count: number
  pages: PageResult[]
}

export interface UploadResponse {
  document_id: string
}
