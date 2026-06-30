'use client'

import { useParams, useRouter } from 'next/navigation'
import { useDocumentReport, usePagination } from '@/lib/hooks'
import { DocumentViewer } from '@/components/document-viewer'
import { ClassificationCard } from '@/components/classification-card'
import { ExtractionCard } from '@/components/extraction-card'
import { SummaryStats } from '@/components/summary-stats'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RefreshCw, Loader2 } from 'lucide-react'

export default function DocumentPage() {
  const params = useParams()
  const router = useRouter()
  const documentId = params.id as string

  const { report, isLoading, error, isProcessing, refetch } =
    useDocumentReport(documentId)

  const { currentPage, totalPages, currentItems, goToPage, nextPage, prevPage } =
    usePagination(report?.pages || [], 1)

  const currentPageData = currentItems[0]

  const handleRefresh = () => {
    refetch()
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.push('/')}
                variant="ghost"
                size="icon"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-foreground">
                  {report?.original_filename || 'Document'}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Document ID: {documentId.slice(0, 8)}...
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isProcessing && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-50 dark:bg-yellow-950/30">
                  <Loader2 className="h-4 w-4 text-yellow-600 dark:text-yellow-500 animate-spin" />
                  <span className="text-sm font-medium text-yellow-700 dark:text-yellow-600">
                    Processing...
                  </span>
                </div>
              )}
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm font-medium text-destructive">{error}</p>
          </div>
        )}

        {isLoading && !report ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="h-8 w-8 text-primary animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading document report...</p>
            </div>
          </div>
        ) : report ? (
          <div className="space-y-8">
            {/* Summary Stats */}
            {/* <section>
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Overview
              </h2>
              <SummaryStats summary={report.summary} />
            </section> */}

            {/* Document Viewer and Analysis */}
            {currentPageData && (
              <section>
                <div className="space-y-4 mb-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-foreground">
                      Page Analysis
                    </h2>
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage} of {totalPages}
                    </span>
                  </div>
                </div>

                {/* Document Viewer */}
                <DocumentViewer
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPrevPage={prevPage}
                  onNextPage={nextPage}
                  onGoToPage={goToPage}
                />

                {/* Classification and Extraction */}
                <div className="mt-8 grid lg:grid-cols-2 gap-6">
                  <ClassificationCard
                  classification={{
                    documentType: currentPageData.document_type,
                    confidence: currentPageData.classification_confidence ?? 0
                    }}
                  />
                  <ExtractionCard extraction={currentPageData.extraction_json} />
                </div>

                {/* Raw Text (if available) */}
                {currentPageData.extraction_json?.raw_ocr_text && (
                  <div className="mt-6 rounded-lg border border-border bg-card p-6">
                    <details className="group cursor-pointer">
                      <summary className="text-sm font-medium text-foreground flex items-center gap-2 hover:text-primary transition-colors">
                        <span className="inline-block transition-transform group-open:rotate-180">
                          ▶
                        </span>
                        Raw Text
                      </summary>
                      <pre className="mt-4 p-4 bg-background rounded-md text-xs text-muted-foreground overflow-auto max-h-96 whitespace-pre-wrap break-words">
                        {currentPageData.extraction_json?.raw_ocr_text}
                      </pre>
                    </details>
                  </div>
                )}
              </section>
            )}

            {/* Pages Navigation */}
            {totalPages > 1 && (
              <section className="mt-8 pt-6 border-t border-border">
                <h3 className="text-sm font-medium text-muted-foreground mb-4">
                  All Pages
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {report.pages.map((page) => (
                    <button
                      key={page.page_number}
                      onClick={() => goToPage(page.page_number)}
                      className={cn(
                        'rounded-lg border p-4 text-center transition-all',
                        currentPage === page.page_number
                          ? 'border-primary bg-primary/10 ring-2 ring-primary'
                          : 'border-border bg-card hover:border-primary/50 hover:bg-muted'
                      )}
                    >
                      <p className="text-sm font-medium text-foreground">
                        Page {page.page_number}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {Math.round(page.classification_confidence ?? 0 / 100)}%
                      </p>
                    </button>
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : null}
      </main>
    </div>
  )
}

function cn(...classes: (string | undefined | boolean)[]) {
  return classes.filter(Boolean).join(' ')
}
