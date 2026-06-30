'use client'

import { useState } from 'react'
import { ChevronDown, Copy, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ExtractionResult } from '@/lib/types'

interface ExtractionCardProps {
  extraction: ExtractionResult
}

export function ExtractionCard({ extraction }: ExtractionCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  const entries = Object.entries(extraction).slice(0, 10)
  const hasMore = Object.entries(extraction).length > 10

  const handleCopy = (key: string, value: any) => {
    const text = `${key}: ${JSON.stringify(value)}`
    navigator.clipboard.writeText(text).then(() => {
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), 2000)
    })
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-muted/50 transition-colors"
      >
        <div>
          <h3 className="font-semibold text-foreground text-left">
            Extracted Data
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {Object.keys(extraction).length} fields extracted
          </p>
        </div>
        <ChevronDown
          className={cn(
            'h-5 w-5 text-muted-foreground transition-transform',
            isExpanded && 'rotate-180'
          )}
        />
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="border-t border-border">
          <div className="p-6 space-y-3 bg-background/50">
            {entries.map(([key, value]) => (
              <div
                key={key}
                className="flex items-start justify-between gap-4 p-3 rounded-md bg-card border border-border hover:border-primary/50 transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {key}
                  </p>
                  <p className="text-sm font-medium text-foreground mt-1 break-words">
                    {typeof value === 'object'
                      ? JSON.stringify(value)
                      : String(value)}
                  </p>
                </div>
                <Button
                  onClick={() => handleCopy(key, value)}
                  variant="ghost"
                  size="sm"
                  className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                >
                  {copiedKey === key ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            ))}

            {hasMore && (
              <div className="p-3 text-center">
                <p className="text-xs text-muted-foreground">
                  +{Object.keys(extraction).length - 10} more fields
                </p>
              </div>
            )}
          </div>

          {/* JSON View */}
          <div className="border-t border-border p-6">
            <details className="group cursor-pointer">
              <summary className="text-sm font-medium text-foreground flex items-center gap-2 hover:text-primary transition-colors">
                <span className="inline-block transition-transform group-open:rotate-180">
                  ▶
                </span>
                View as JSON
              </summary>
              <pre className="mt-3 p-3 bg-muted rounded-md text-xs overflow-auto max-h-64 text-muted-foreground">
                {JSON.stringify(extraction, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  )
}
