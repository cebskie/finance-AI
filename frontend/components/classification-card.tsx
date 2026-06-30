'use client'

import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ClassificationResult } from '@/lib/types'

interface ClassificationCardProps {
  classification: ClassificationResult
}

export function ClassificationCard({
  classification,
}: ClassificationCardProps) {
  const confidenceColor =
    classification.confidence > 0.8
      ? 'text-green-600'
      : classification.confidence > 0.6
        ? 'text-yellow-600'
        : 'text-orange-600'

  const confidencePercentage = Math.round(classification.confidence)

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-foreground">Classification</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Document type and metadata
            </p>
          </div>
          <div className="text-right">
            <p className={`text-2xl font-bold ${confidenceColor}`}>
              {confidencePercentage}%
            </p>
            <p className="text-xs text-muted-foreground">Confidence</p>
          </div>
        </div>

        {/* Document Type */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">
            Document Type
          </label>
          <div className="inline-block rounded-md bg-primary/10 px-3 py-2">
            <p className="font-medium text-primary">
              {classification.documentType}
            </p>
          </div>
        </div>

        {/* Tags */}
        {classification.tags && classification.tags.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              Tags
            </label>
            <div className="flex flex-wrap gap-2">
              {classification.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence Indicator */}
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">
              Model Confidence
            </span>
            <span className="text-xs font-semibold text-foreground">
              {confidencePercentage}%
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
            <div
              className={cn(
                'h-full transition-all',
                confidencePercentage > 80
                  ? 'bg-green-500'
                  : confidencePercentage > 60
                    ? 'bg-yellow-500'
                    : 'bg-orange-500'
              )}
              style={{ width: `${confidencePercentage}%` }}
            />
          </div>
        </div>

        {/* Confidence Note */}
        {confidencePercentage < 80 && (
          <div className="flex gap-2 rounded-md bg-yellow-50 dark:bg-yellow-950/30 p-3">
            <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-700 dark:text-yellow-600">
              Lower confidence score. Results should be reviewed.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}


