'use client'

import { FileText, CheckCircle2, Database } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ProcessingReport } from '@/lib/types'

interface SummaryStatsProps {
  report: ProcessingReport
}

export function SummaryStats({ report }: SummaryStatsProps) {
  const stats = [
    {
      icon: FileText,
      label: 'Filename',
      value: report.original_filename,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
    },
    {
      icon: CheckCircle2,
      label: 'Page Count',
      value: report.page_count,
      color: 'text-green-600',
      bg: 'bg-green-50 dark:bg-green-950/30',
    },
    {
      icon: Database,
      label: 'Document ID',
      value: report.document_id,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50 dark:bg-indigo-950/30',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-foreground">Document Summary</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Uploaded document details
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-primary">{report.page_count}</p>
            <p className="text-xs text-muted-foreground">Pages</p>
          </div>
        </div>
        <div className="mt-4 h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-500"
            style={{ width: '100%' }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {report.original_filename}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, idx) => {
          const Icon = stat.icon
          return (
            <div
              key={idx}
              className={cn(
                'rounded-lg border border-border p-4 transition-all hover:border-primary/50',
                stat.bg
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('p-2 rounded-md bg-white dark:bg-black/20')}>
                  <Icon className={cn('h-5 w-5', stat.color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {stat.label}
                  </p>
                  <p className="text-2xl font-bold text-foreground mt-1 break-words">
                    {stat.value}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="font-semibold text-foreground">Processing Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-t border-border hover:bg-muted/50 transition-colors">
                <td className="px-6 py-3 font-medium text-muted-foreground">
                  Total Pages
                </td>
                <td className="px-6 py-3 text-right font-semibold text-foreground">
                  {report.page_count}
                </td>
              </tr>
              <tr className="border-t border-border hover:bg-muted/50 transition-colors">
                <td className="px-6 py-3 font-medium text-muted-foreground">
                  Filename
                </td>
                <td className="px-6 py-3 text-right font-semibold text-green-600 break-words">
                  {report.original_filename}
                </td>
              </tr>
              <tr className="border-t border-border hover:bg-muted/50 transition-colors">
                <td className="px-6 py-3 font-medium text-muted-foreground">
                  Document ID
                </td>
                <td className="px-6 py-3 text-right font-semibold text-indigo-600 break-words">
                  {report.document_id}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
