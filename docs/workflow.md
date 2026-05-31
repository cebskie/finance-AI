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

This endpoint does not start OCR or extraction yet.
