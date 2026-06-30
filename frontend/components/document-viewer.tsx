'use client'

import { FileText, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface DocumentViewerProps {
  currentPage: number
  totalPages: number
  onPrevPage: () => void
  onNextPage: () => void
  onGoToPage: (page: number) => void
}

export function DocumentViewer({
  currentPage,
  totalPages,
  onPrevPage,
  onNextPage,
  onGoToPage,
}: DocumentViewerProps) {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10)
    if (!isNaN(value)) {
      onGoToPage(value)
    }
  }

  return (
    <div className="w-full space-y-4">
      {/* PDF Viewer */}
      <div className="rounded-lg border border-border bg-card p-8">
        <div className="flex items-center justify-center min-h-96 bg-muted rounded-md">
          <div className="flex flex-col items-center gap-3 text-muted-foreground">
            <FileText className="h-16 w-16 opacity-50" />
            <div className="text-center">
              <p className="font-semibold">Page {currentPage}</p>
              <p className="text-sm">
                PDF rendering would be implemented here with react-pdf
              </p>
              <p className="text-xs mt-1">
                Demo shows structure only
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-lg border border-border bg-card p-4">
        <Button
          onClick={onPrevPage}
          disabled={currentPage === 1}
          variant="outline"
          size="sm"
          className="sm:w-auto w-full"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>

        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Page</span>
          <input
            type="number"
            min="1"
            max={totalPages}
            value={currentPage}
            onChange={handleInputChange}
            className={cn(
              'w-16 rounded border border-border bg-background px-2 py-1 text-center text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary'
            )}
          />
          <span className="text-sm text-muted-foreground">of {totalPages}</span>
        </div>

        <Button
          onClick={onNextPage}
          disabled={currentPage === totalPages}
          variant="outline"
          size="sm"
          className="sm:w-auto w-full"
        >
          Next
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  )
}
