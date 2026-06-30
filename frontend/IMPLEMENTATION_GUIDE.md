# Implementation Guide

This guide explains the architecture, patterns, and how to extend the Document Intelligence Platform frontend.

## Project Architecture

```
Frontend (Next.js 16)
├── Components (React 19)
│   ├── Upload Zone (drag-drop UI)
│   ├── Document Viewer (page navigation)
│   ├── Classification Card (results display)
│   ├── Extraction Card (JSON extraction)
│   └── Summary Stats (analytics dashboard)
├── Custom Hooks (lib/hooks.ts)
│   ├── useDocumentUpload
│   ├── useDocumentReport
│   └── usePagination
├── Types (lib/types.ts)
│   └── TypeScript interfaces for all API responses
└── Pages
    ├── / (home - upload)
    └── /documents/[id] (details - results)
```

## Data Flow

### Upload Flow

```
User selects file
    ↓
UploadZone component calls onFileSelect
    ↓
useDocumentUpload.uploadFile()
    ↓
XMLHttpRequest to POST /documents/upload
    ↓
Backend stores file, returns documentId
    ↓
setDocumentId(documentId)
    ↓
useRouter.push('/documents/{id}')
    ↓
Document details page loads
```

### Processing Report Flow

```
Document page loads with [id]
    ↓
useDocumentReport(documentId) hook initializes
    ↓
fetchReport() makes initial GET request
    ↓
Response: { document, pages, summary }
    ↓
usePagination creates page array
    ↓
Display classification/extraction for current page
    ↓
If processingStatus === 'processing'
    ↓
Set up 2-second polling interval
    ↓
Update state as pages are processed
    ↓
When complete, stop polling
```

## Core Components Explained

### UploadZone Component

**Purpose**: Handles file upload with drag-drop support

**Props**:
- `onFileSelect(file)`: Callback when file is selected
- `isUploading`: Loading state
- `progress`: Upload percentage 0-100
- `error`: Error message string
- `documentId`: Successful upload ID

**Features**:
- Drag-and-drop detection
- File type validation (PDF only)
- Real-time progress bar
- Success/error notifications
- Accessible with proper ARIA labels

**Extension Points**:
- Add file size validation
- Support additional file types
- Custom progress visualization

### DocumentViewer Component

**Purpose**: Shows document pages with navigation

**Props**:
- `currentPage`: Current page number
- `totalPages`: Total number of pages
- `onPrevPage()`: Previous button handler
- `onNextPage()`: Next button handler
- `onGoToPage(page)`: Jump to specific page

**Features**:
- Keyboard-friendly navigation
- Input validation for page jumps
- Disabled states for boundary pages
- Shows current/total pages

**To Integrate Real PDF Rendering**:

```typescript
import { Document, Page, pdfjs } from 'react-pdf'

// Set worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

// In component
<Document file={pdfUrl}>
  <Page pageNumber={currentPage} />
</Document>
```

### ClassificationCard Component

**Purpose**: Displays document classification results

**Displays**:
- Document type
- Confidence score with color coding
- Tag/category badges
- Confidence progress bar
- Warning for low confidence

**Customization**:
- Change color thresholds in confidence logic
- Add icons for different document types
- Modify tag styling

### ExtractionCard Component

**Purpose**: Shows extracted structured data

**Features**:
- Key-value pair display
- Copy-to-clipboard for each field
- JSON view toggle
- Scrollable with max height
- Collapsible layout

**Customization**:
- Add field validation formatting
- Custom field renderers
- Export options (CSV, JSON)

### SummaryStats Component

**Purpose**: Analytics dashboard with overview metrics

**Metrics Displayed**:
- Processing status progress bar
- Total/processed/failed pages
- Average confidence
- Entities extracted
- Processing time

**Cards Grid**:
- Responsive 1-2-3 column layout
- Color-coded by metric type
- Details table view

## Custom Hooks

### useDocumentUpload()

Manages file upload lifecycle with progress tracking.

```typescript
const {
  uploadFile,      // async (file: File) => Promise<void>
  isUploading,     // boolean
  progress,        // 0-100
  error,           // string | null
  documentId,      // string | null
  reset            // () => void
} = useDocumentUpload()
```

**Implementation Details**:
- Uses XMLHttpRequest for progress tracking
- FormData for multipart file upload
- Tracks upload and network progress
- Handles errors gracefully

**Extension**:
```typescript
// Add retry logic
const handleRetry = () => {
  reset()
  uploadFile(file)
}
```

### useDocumentReport(documentId)

Fetches processing report with auto-polling.

```typescript
const {
  report,        // ProcessingReport | null
  isLoading,     // boolean
  error,         // string | null
  isProcessing,  // boolean
  refetch        // () => Promise<void>
} = useDocumentReport(documentId)
```

**Features**:
- Automatic polling when processing
- 2-second poll interval
- Stops when complete
- Cleanup on unmount
- Manual refetch capability

**Customization**:
```typescript
// Change poll interval
const POLL_INTERVAL = 5000 // 5 seconds
// Edit in lib/hooks.ts

// Or expose as parameter
export function useDocumentReport(
  documentId: string | null,
  pollInterval: number = 2000
)
```

### usePagination(items, itemsPerPage)

Manages pagination state and navigation.

```typescript
const {
  currentPage,   // number (1-based)
  totalPages,    // number
  currentItems,  // any[] (items for current page)
  goToPage,      // (page: number) => void
  nextPage,      // () => void
  prevPage       // () => void
} = usePagination(items, itemsPerPage)
```

**Default**: 1 item per page (for page-by-page viewing)

## TypeScript Types

All types are defined in `lib/types.ts`. Key types:

```typescript
// API Response
interface UploadResponse {
  documentId: string
  message: string
}

// Document metadata
interface Document {
  id: string
  filename: string
  uploadedAt: string
  totalPages: number
  processingStatus: 'processing' | 'completed' | 'failed'
  errorMessage?: string
}

// Page-level results
interface PageResult {
  pageNumber: number
  classification: ClassificationResult
  extraction: ExtractionResult
  rawText?: string
}

// Complete report
interface ProcessingReport {
  document: Document
  pages: PageResult[]
  summary: SummaryStatistics
}
```

## Environment Configuration

Create `.env.local`:

```env
# Required - Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:3001

# Optional - Enable development features
NEXT_PUBLIC_DEBUG=true
```

### Production Deployment

For Vercel:

1. Add environment variable in Vercel dashboard
2. Set `NEXT_PUBLIC_API_URL` to your production backend

For other platforms:
- Build with environment variable set
- Or use dynamic configuration at runtime

## Styling System

### Color Scheme

Professional blue-based theme defined in `app/globals.css`:

```css
/* Primary (Deep Blue) */
--primary: oklch(0.24 0.187 254.604);

/* Secondary (Light Purple) */
--secondary: oklch(0.95 0.011 257.314);

/* Accent (Bright Blue) */
--accent: oklch(0.58 0.194 249.659);
```

### Customization

Edit color tokens in `globals.css`:

```css
:root {
  --primary: oklch(0.xx 0.xxx 254.604); /* Change this */
}
```

### Typography

Two fonts via `app/layout.tsx`:

```typescript
const geistSans = Geist({ variable: '--font-geist-sans' })
const geistMono = Geist_Mono({ variable: '--font-geist-mono' })
```

Change fonts:

```typescript
import { YourFont } from 'next/font/google'
const customFont = YourFont({ variable: '--font-sans' })
```

## Performance Optimizations

### Current

- Code splitting via Next.js routes
- Client-side hooks prevent unnecessary API calls
- Polling only when processing
- Responsive images with Tailwind

### Potential Enhancements

```typescript
// Memoize expensive components
const AnalysisCard = React.memo(ClassificationCard)

// Use useMemo for data transformations
const sortedPages = useMemo(
  () => pages.sort((a, b) => a.pageNumber - b.pageNumber),
  [pages]
)

// Lazy load statistics
const SummaryStats = dynamic(
  () => import('@/components/summary-stats'),
  { ssr: false }
)
```

## Error Handling

### Patterns Used

1. **Network Errors**: Displayed in UI with retry option
2. **API Errors**: Parsed and shown to user
3. **Type Errors**: Caught by TypeScript in development

### Enhancement

Add error boundary:

```typescript
'use client'

import { Component } from 'react'

export class ErrorBoundary extends Component {
  componentDidCatch(error, info) {
    console.error('Error:', error)
  }

  render() {
    return <div>{this.props.children}</div>
  }
}
```

## Testing

### Component Testing

```typescript
import { render, screen } from '@testing-library/react'
import { UploadZone } from '@/components/upload-zone'

test('renders upload zone', () => {
  render(<UploadZone {...props} />)
  expect(screen.getByText(/Drop your PDF/)).toBeInTheDocument()
})
```

### Hook Testing

```typescript
import { renderHook, act } from '@testing-library/react'
import { useDocumentUpload } from '@/lib/hooks'

test('uploads file with progress', () => {
  const { result } = renderHook(() => useDocumentUpload())

  act(() => {
    result.current.uploadFile(mockFile)
  })

  expect(result.current.isUploading).toBe(true)
})
```

### E2E Testing

```typescript
// With Playwright
test('upload document and view results', async ({ page }) => {
  await page.goto('/');
  await page.setInputFiles('input[type="file"]', 'test.pdf');
  await page.click('button:has-text("Select File")');
  await page.waitForURL('/documents/*');
  expect(await page.locator('text=Overview')).toBeVisible();
})
```

## Deployment Checklist

- [ ] Update `NEXT_PUBLIC_API_URL` to production backend
- [ ] Set appropriate timeout values
- [ ] Add analytics tracking
- [ ] Configure CSP headers
- [ ] Test with production backend
- [ ] Monitor error logs
- [ ] Set up performance monitoring
- [ ] Test on target browsers
- [ ] Verify responsive design
- [ ] Check accessibility

## Common Extensions

### Add Export Functionality

```typescript
// Add to extraction-card.tsx
const exportAsJSON = () => {
  const json = JSON.stringify(extraction, null, 2)
  downloadFile(json, 'extraction.json')
}

const downloadFile = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
}
```

### Add Document History

```typescript
// Create lib/storage.ts
export function saveToHistory(documentId: string) {
  const history = JSON.parse(
    localStorage.getItem('documentHistory') || '[]'
  )
  history.unshift({ id: documentId, timestamp: Date.now() })
  localStorage.setItem('documentHistory', JSON.stringify(history.slice(0, 10)))
}

// Use in documents/[id]/page.tsx
useEffect(() => {
  if (report?.document.id) {
    saveToHistory(report.document.id)
  }
}, [report?.document.id])
```

### Add Real-time Updates with WebSocket

```typescript
// Create lib/websocket.ts
export function useWebSocketReport(documentId: string | null) {
  const [report, setReport] = useState<ProcessingReport | null>(null)

  useEffect(() => {
    if (!documentId) return

    const ws = new WebSocket(
      `${API_BASE_URL.replace('http', 'ws')}/ws/${documentId}`
    )

    ws.onmessage = (e) => {
      setReport(JSON.parse(e.data))
    }

    return () => ws.close()
  }, [documentId])

  return { report }
}
```

## Support & Debugging

### Enable Debug Logging

Add debug statements throughout the code:

```typescript
if (process.env.NEXT_PUBLIC_DEBUG) {
  console.log('[v0] Report updated:', report)
}
```

### Check Console

The browser console will show:
- API request/response logs
- Component lifecycle events
- Error messages

### Check Network Tab

In DevTools:
1. Look at Network tab
2. Verify API requests to correct URL
3. Check response payloads match types
4. Monitor polling requests

## Questions & Support

Refer to:
- `README.md` for setup and features
- `MOCK_API_EXAMPLE.md` for API format
- Component JSDoc comments for usage
- Type definitions for data structure

---

**Happy building!** 🚀
