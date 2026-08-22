'use client'

import { useState } from 'react'
import DocumentUpload from '@/components/DocumentUpload'
import QueryInterface from '@/components/QueryInterface'
import DocumentList from '@/components/DocumentList'
import { FileText, MessageSquare, List } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'query' | 'documents'>('upload')
  const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([])

  const handleDocumentUploaded = (document: any) => {
    setUploadedDocuments(prev => [...prev, document])
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                📄 Document Intelligence
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AI-powered document processing and analysis
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                ✓ Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-sm p-1 flex space-x-2">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-md transition-all ${
              activeTab === 'upload'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <FileText className="w-5 h-5" />
            <span className="font-medium">Upload Document</span>
          </button>
          <button
            onClick={() => setActiveTab('query')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-md transition-all ${
              activeTab === 'query'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <MessageSquare className="w-5 h-5" />
            <span className="font-medium">Query Documents</span>
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-md transition-all ${
              activeTab === 'documents'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <List className="w-5 h-5" />
            <span className="font-medium">Documents ({uploadedDocuments.length})</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {activeTab === 'upload' && (
          <DocumentUpload onDocumentUploaded={handleDocumentUploaded} />
        )}
        {activeTab === 'query' && (
          <QueryInterface />
        )}
        {activeTab === 'documents' && (
          <DocumentList documents={uploadedDocuments} />
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            SIH 2024 - Document Intelligence System
          </p>
        </div>
      </footer>
    </main>
  )
}
