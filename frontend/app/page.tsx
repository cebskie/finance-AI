'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useDocumentUpload } from '@/lib/hooks'
import { UploadZone } from '@/components/upload-zone'
import { FileText, Zap, BarChart3 } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const { uploadFile, isUploading, progress, error, documentId } =
    useDocumentUpload()

  useEffect(() => {
    if (documentId) {
      router.push(`/documents/${documentId}`)
    }
  }, [documentId, router])

  const handleFileSelect = async (file: File) => {
    await uploadFile(file)
  }

  // Redirect to document page when upload is complete
  // if (documentId) {
  //   router.push(`/documents/${documentId}`)
  // }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary p-2">
              <FileText className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                Document Intelligence
              </h1>
              <p className="text-sm text-muted-foreground">
                AI-powered classification and data extraction
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-foreground mb-4 text-pretty">
            Intelligent Document Processing
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Upload your PDF documents and get instant AI-powered classification,
            data extraction, and comprehensive analytics in seconds.
          </p>
        </div>

        {/* Upload Section */}
        <div className="flex justify-center mb-16">
          <UploadZone
            onFileSelect={handleFileSelect}
            isUploading={isUploading}
            progress={progress}
            error={error}
            documentId={documentId}
          />
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon={FileText}
            title="Smart Classification"
            description="Automatically categorize documents with AI-powered classification engine"
          />
          <FeatureCard
            icon={Zap}
            title="Data Extraction"
            description="Extract structured data and key information from documents instantly"
          />
          <FeatureCard
            icon={BarChart3}
            title="Analytics Dashboard"
            description="View comprehensive processing statistics and confidence metrics"
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-muted-foreground">
            Document Intelligence Platform • Powered by Advanced AI Models
          </p>
        </div>
      </footer>
    </div>
  )
}

interface FeatureCardProps {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
}

function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 hover:border-primary/50 transition-colors">
      <div className="rounded-lg bg-primary/10 p-3 w-fit mb-4">
        <Icon className="h-6 w-6 text-primary" />
      </div>
      <h3 className="font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  )
}
