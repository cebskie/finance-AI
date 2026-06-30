# Document Intelligence Platform

A modern, production-ready React frontend for an AI-powered document intelligence platform. Upload PDFs to get instant AI-driven classification, data extraction, and comprehensive analytics.

## Features

- **📄 PDF Upload**: Drag-and-drop or click-to-upload interface with real-time progress tracking
- **🔍 Document Classification**: AI-powered automatic document type classification with confidence scores
- **📊 Data Extraction**: Structured data extraction from documents displayed in multiple formats
- **📈 Analytics Dashboard**: Comprehensive statistics including processing metrics and confidence analysis
- **📖 Page-by-Page Analysis**: View classification and extraction results for each document page
- **🎨 Modern UI**: Professional design with Tailwind CSS and shadcn/ui components
- **⚡ Real-time Polling**: Live processing status updates every 2 seconds
- **📱 Responsive Design**: Fully responsive interface for desktop, tablet, and mobile
- **🔒 Type-Safe**: Full TypeScript support with strict mode enabled

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI Framework**: React 19
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui
- **Language**: TypeScript
- **HTTP Client**: Fetch API with custom hooks
- **Icons**: Lucide React

## Project Structure

```
├── app/
│   ├── layout.tsx              # Root layout with metadata
│   ├── page.tsx                # Home page with upload zone
│   ├── globals.css             # Global styles and theme tokens
│   └── documents/
│       └── [id]/
│           └── page.tsx        # Document details page
├── components/
│   ├── ui/
│   │   └── button.tsx          # shadcn Button component
│   ├── upload-zone.tsx         # Drag-drop file upload
│   ├── document-viewer.tsx     # PDF page viewer with navigation
│   ├── classification-card.tsx # Classification results display
│   ├── extraction-card.tsx     # Extraction results display
│   └── summary-stats.tsx       # Analytics dashboard
├── lib/
│   ├── types.ts                # TypeScript type definitions
│   ├── hooks.ts                # Custom React hooks (useDocumentUpload, etc.)
│   └── utils.ts                # Utility functions (cn, etc.)
└── public/                     # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- pnpm, npm, yarn, or Bun package manager

### Installation

1. **Clone and install dependencies**:
   ```bash
   pnpm install
   # or: npm install, yarn install, bun install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Configure `NEXT_PUBLIC_API_URL` to point to your backend API:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:3001
   ```

3. **Run the development server**:
   ```bash
   pnpm dev
   # or: npm run dev, yarn dev, bun dev
   ```

4. **Open in browser**:
   Navigate to `http://localhost:3000` in your browser.

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL` (required): Backend API base URL (e.g., `http://localhost:3001`)
- `NEXT_PUBLIC_DEBUG` (optional): Enable debug logging (`true`/`false`)
- `NEXT_PUBLIC_API_TOKEN` (optional): API authentication token if needed

## API Integration

The frontend expects a backend API with the following endpoints:

### Upload Document
```
POST /documents/upload
Content-Type: multipart/form-data

Request:
- file: File (PDF)

Response:
{
  "documentId": "string",
  "message": "string"
}
```

### Get Processing Report
```
GET /documents/{id}/processing-report

Response:
{
  "document": {
    "id": "string",
    "filename": "string",
    "uploadedAt": "ISO8601",
    "totalPages": "number",
    "processingStatus": "processing|completed|failed",
    "errorMessage": "string (optional)"
  },
  "pages": [
    {
      "pageNumber": "number",
      "classification": {
        "documentType": "string",
        "confidence": "number (0-1)",
        "tags": ["string"]
      },
      "extraction": {
        "key1": "value1",
        "key2": "value2"
      },
      "rawText": "string (optional)"
    }
  ],
  "summary": {
    "totalPages": "number",
    "processedPages": "number",
    "failedPages": "number",
    "averageConfidence": "number (0-1)",
    "extractedEntities": "number",
    "processingTimeMs": "number"
  }
}
```

## Features Explained

### Upload Zone Component
- Drag-and-drop support for PDF files
- File size validation (max 50MB)
- Real-time upload progress tracking
- Success/error notifications
- Accessible file input

### Document Viewer
- Page navigation (previous, next, go to page)
- Shows placeholder for PDF rendering (integrate react-pdf for actual rendering)
- Current page indicator
- Total pages counter

### Classification Card
- Document type display
- Confidence score with color coding
- Tag/category badges
- Confidence indicator bar
- Low confidence warning alert

### Extraction Card
- Key-value pair display
- Copy-to-clipboard functionality
- JSON view with syntax highlighting
- Collapsible layout
- Scrollable with max height

### Summary Statistics
- Processing status progress bar
- 6 statistics cards with icons
- Processing details table
- Color-coded metrics
- Success rate calculation

### Document Details Page
- Real-time processing status
- Auto-refresh capability
- Page-by-page navigation
- Back navigation to home
- Loading and error states
- Page thumbnail grid

## Hooks Reference

### useDocumentUpload()
Manages file upload with progress tracking.

```typescript
const {
  uploadFile,      // (file: File) => Promise<void>
  isUploading,     // boolean
  progress,        // 0-100
  error,           // string | null
  documentId,      // string | null
  reset            // () => void
} = useDocumentUpload()
```

### useDocumentReport(documentId)
Fetches and polls processing report.

```typescript
const {
  report,        // ProcessingReport | null
  isLoading,     // boolean
  error,         // string | null
  isProcessing,  // boolean
  refetch        // () => Promise<void>
} = useDocumentReport(documentId)
```

### usePagination(items, itemsPerPage)
Manages pagination state.

```typescript
const {
  currentPage,   // number
  totalPages,    // number
  currentItems,  // any[]
  goToPage,      // (page: number) => void
  nextPage,      // () => void
  prevPage       // () => void
} = usePagination(items, 1)
```

## Styling

The project uses a professional theme with:
- **Primary**: Deep blue (#3D4FDB)
- **Secondary**: Light purple tint
- **Accent**: Brighter blue
- **Neutrals**: White, grays, and dark backgrounds
- **Status Colors**: Green (success), Yellow (warning), Orange (caution), Red (error)

### Dark Mode
Automatic dark mode support based on system preferences with fallback to light mode.

## Performance Optimizations

- Code splitting with Next.js dynamic imports
- Optimized images and lazy loading
- Client-side hooks for efficient state management
- Polling only when document is processing
- Responsive design prevents unnecessary renders

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Modern mobile browsers

## Production Build

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

## Deployment

The frontend can be deployed to:
- **Vercel** (recommended): Automatic deployments from Git
- **Netlify**: Similar to Vercel with Git integration
- **AWS Amplify**: AWS-hosted deployment
- **Traditional servers**: Build and serve with Node.js

Example Vercel deployment:
```bash
vercel deploy
```

## Customization

### Changing the Theme
Edit `/app/globals.css` to modify color tokens:
```css
:root {
  --primary: oklch(0.24 0.187 254.604);
  /* Update other colors... */
}
```

### Adding PDF Rendering
Install react-pdf and configure in `components/document-viewer.tsx`:
```bash
pnpm add react-pdf
```

### API Error Handling
Customize error messages in the hooks (`lib/hooks.ts`) or components as needed.

## Testing

```bash
# Run tests (when configured)
pnpm test

# Run with coverage
pnpm test:coverage
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on the project repository.

---

**Built with Next.js, React, and TypeScript** ✨
