# Mock API Example for Testing

This document provides example responses and a simple Node.js mock server for testing the frontend without a real backend.

## Quick Start with Mock Server

### Install Express (if not already installed)

```bash
npm install express --save-dev
# or with pnpm/yarn
pnpm add -D express
```

### Create a Mock Server

Save this as `mock-server.js` in your project root:

```javascript
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Enable CORS for development
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// Mock data storage
const documents = new Map();

// POST /documents/upload
app.post('/documents/upload', (req, res) => {
  // Simulate file upload
  const documentId = 'doc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  
  // Store document info
  documents.set(documentId, {
    id: documentId,
    filename: req.body.filename || 'document.pdf',
    uploadedAt: new Date().toISOString(),
    totalPages: Math.floor(Math.random() * 10) + 2,
    processingStatus: 'processing',
    startTime: Date.now(),
  });

  res.json({
    documentId,
    message: 'Document uploaded successfully and queued for processing',
  });
});

// GET /documents/:id/processing-report
app.get('/documents/:id/processing-report', (req, res) => {
  const { id } = req.params;
  const doc = documents.get(id);

  if (!doc) {
    return res.status(404).json({
      error: 'Document not found',
      details: `No document with ID: ${id}`,
    });
  }

  // Simulate processing over time (completes after 10 seconds)
  const elapsedTime = Date.now() - doc.startTime;
  const isComplete = elapsedTime > 10000;
  const processingStatus = isComplete ? 'completed' : 'processing';
  
  // Calculate processed pages based on elapsed time
  const processedPages = isComplete 
    ? doc.totalPages 
    : Math.min(Math.floor((elapsedTime / 10000) * doc.totalPages) + 1, doc.totalPages);

  const pages = Array.from({ length: doc.totalPages }, (_, i) => ({
    pageNumber: i + 1,
    classification: {
      documentType: ['Invoice', 'Receipt', 'Contract', 'Report', 'Letter'][Math.floor(Math.random() * 5)],
      confidence: 0.75 + Math.random() * 0.24,
      tags: [
        ['financial', 'billing', 'accounting'][Math.floor(Math.random() * 3)],
        ['2024', 'important'][Math.floor(Math.random() * 2)],
      ],
    },
    extraction: {
      company_name: 'Example Corporation Inc.',
      invoice_number: `INV-${1000 + i + 1}`,
      date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0],
      amount: `$${(Math.random() * 10000).toFixed(2)}`,
      status: 'paid',
      vendor_name: 'Supplier Company Ltd.',
      items_count: Math.floor(Math.random() * 20) + 1,
      po_number: `PO-${5000 + Math.floor(Math.random() * 5000)}`,
      due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    rawText: 'Sample raw text extracted from page...\nThis would contain the actual OCR text from the document.',
  }));

  const summary = {
    totalPages: doc.totalPages,
    processedPages,
    failedPages: 0,
    averageConfidence: 0.82,
    extractedEntities: processedPages * Math.floor(Math.random() * 10) + 20,
    processingTimeMs: elapsedTime,
  };

  res.json({
    document: {
      ...doc,
      processingStatus,
    },
    pages: pages.slice(0, processedPages), // Only return processed pages
    summary,
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`\nTesting endpoints:`);
  console.log(`  POST http://localhost:${PORT}/documents/upload`);
  console.log(`  GET  http://localhost:${PORT}/documents/{id}/processing-report`);
  console.log(`  GET  http://localhost:${PORT}/health`);
});
```

### Run the Mock Server

```bash
# In a new terminal
node mock-server.js
```

Or add to `package.json` scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "mock-api": "node mock-server.js",
    "dev:with-mock": "npm run mock-api & npm run dev"
  }
}
```

Then run:
```bash
pnpm dev:with-mock
```

## API Response Examples

### Upload Response

```json
{
  "documentId": "doc_1719293847123_abc123def",
  "message": "Document uploaded successfully and queued for processing"
}
```

### Processing Report Response (In Progress)

```json
{
  "document": {
    "id": "doc_1719293847123_abc123def",
    "filename": "invoice_2024.pdf",
    "uploadedAt": "2024-06-25T10:30:47.123Z",
    "totalPages": 5,
    "processingStatus": "processing",
    "errorMessage": null
  },
  "pages": [
    {
      "pageNumber": 1,
      "classification": {
        "documentType": "Invoice",
        "confidence": 0.92,
        "tags": ["financial", "2024"]
      },
      "extraction": {
        "company_name": "Example Corporation Inc.",
        "invoice_number": "INV-1001",
        "date": "2024-06-20",
        "amount": "$5,234.50",
        "status": "paid",
        "vendor_name": "Supplier Company Ltd.",
        "items_count": 12,
        "po_number": "PO-6234",
        "due_date": "2024-07-20"
      },
      "rawText": "INVOICE\n\nInvoice #: INV-1001\n..."
    }
  ],
  "summary": {
    "totalPages": 5,
    "processedPages": 2,
    "failedPages": 0,
    "averageConfidence": 0.87,
    "extractedEntities": 45,
    "processingTimeMs": 5234
  }
}
```

### Processing Report Response (Complete)

```json
{
  "document": {
    "id": "doc_1719293847123_abc123def",
    "filename": "invoice_2024.pdf",
    "uploadedAt": "2024-06-25T10:30:47.123Z",
    "totalPages": 5,
    "processingStatus": "completed",
    "errorMessage": null
  },
  "pages": [
    {
      "pageNumber": 1,
      "classification": {
        "documentType": "Invoice",
        "confidence": 0.92,
        "tags": ["financial", "2024"]
      },
      "extraction": {
        "company_name": "Example Corporation Inc.",
        "invoice_number": "INV-1001",
        "date": "2024-06-20",
        "amount": "$5,234.50",
        "status": "paid",
        "vendor_name": "Supplier Company Ltd.",
        "items_count": 12,
        "po_number": "PO-6234",
        "due_date": "2024-07-20"
      },
      "rawText": "INVOICE\n\nInvoice #: INV-1001\n..."
    },
    {
      "pageNumber": 2,
      "classification": {
        "documentType": "Invoice",
        "confidence": 0.88,
        "tags": ["financial", "2024"]
      },
      "extraction": {
        "company_name": "Example Corporation Inc.",
        "invoice_number": "INV-1002",
        "date": "2024-06-21",
        "amount": "$3,125.75",
        "status": "pending",
        "vendor_name": "Supplier Company Ltd.",
        "items_count": 8,
        "po_number": "PO-6235",
        "due_date": "2024-07-21"
      },
      "rawText": "INVOICE\n\nInvoice #: INV-1002\n..."
    }
  ],
  "summary": {
    "totalPages": 5,
    "processedPages": 5,
    "failedPages": 0,
    "averageConfidence": 0.89,
    "extractedEntities": 125,
    "processingTimeMs": 12450
  }
}
```

### Error Response

```json
{
  "error": "Document not found",
  "details": "No document with ID: invalid_id"
}
```

## Testing with cURL

### Upload a document
```bash
curl -X POST http://localhost:3001/documents/upload \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.pdf"}'
```

### Get processing report
```bash
curl http://localhost:3001/documents/doc_1719293847123_abc123def/processing-report
```

## Environment Configuration

Set in your `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

## Integration with Real Backend

Once your actual backend is ready:

1. Update `NEXT_PUBLIC_API_URL` to point to your backend
2. Verify the API implements the same endpoints with the documented response format
3. The frontend code won't require any changes - it just uses the environment variable

## Troubleshooting

### CORS Errors
- Make sure the mock server has CORS headers (included in the example above)
- Ensure `NEXT_PUBLIC_API_URL` is correctly set

### Port Already in Use
```bash
# Change port in the command
PORT=3002 node mock-server.js

# And update .env.local
NEXT_PUBLIC_API_URL=http://localhost:3002
```

### Document ID Not Found
- Use the actual ID returned from the upload endpoint
- IDs are prefixed with `doc_` followed by timestamp and random string
