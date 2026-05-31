# Upload Workflow

## PDF Upload MVP

The upload API accepts one PDF file, validates it, stores the object in MinIO,
and persists document metadata in Postgres.

Endpoint:

```text
POST /api/v1/documents
```

Multipart form field:

```text
file
```

Validation rules:

- filename must end with `.pdf`
- content type must be `application/pdf`
- file cannot be empty
- file size must be less than or equal to `MAX_UPLOAD_BYTES`
- file bytes must start with the PDF magic header `%PDF-`

Storage:

- bucket is configured with `DOCUMENT_BUCKET`
- object key format is `documents/{document_id}/{original_filename}`

Database:

- metadata is persisted to the `documents` table
- initial document status is `uploaded`

After the original PDF is stored and the document metadata row is created, the
upload workflow retrieves the PDF from MinIO and invokes page splitting.

Successful upload status progression:

```text
uploaded -> processing_pages -> pages_ready
```

If page splitting fails after the original PDF and document row are persisted,
the document is retained and marked:

```text
page_split_failed
```

This endpoint does not start OCR or extraction yet.

## PDF Page Splitting MVP

The page splitting service converts persisted PDF bytes into one PNG image per
page using `pdf2image`.

Service:

```text
PdfPageSplittingService.split_pdf(document, pdf_content)
```

Output behavior:

- converts PDF pages at `PDF_SPLIT_DPI`
- stores each page image in MinIO as `image/png`
- persists page metadata in the `document_pages` table

Page object key format:

```text
documents/{document_id}/pages/page-0001.png
```

Runtime dependency:

- Docker installs `poppler-utils`
- local development needs Poppler available on `PATH`, or `POPPLER_PATH`
  configured to the Poppler binary directory

The service is currently triggered synchronously by the PDF upload workflow.
It is not yet wired into an async processing job.
