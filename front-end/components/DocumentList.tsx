'use client'

import { FileText, Calendar, CheckCircle, AlertCircle } from 'lucide-react'

interface DocumentListProps {
  documents: any[]
}

export default function DocumentList({ documents }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
        <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded</h3>
        <p className="text-sm text-gray-600">
          Upload your first document to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Uploaded Documents ({documents.length})
        </h3>
      </div>

      <div className="grid gap-4">
        {documents.map((doc, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 rounded-lg p-3">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      Document #{index + 1}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      ID: {doc.document_id?.substring(0, 8)}...
                    </p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  doc.status === 'success'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {doc.status === 'success' ? '✓ Processed' : '✗ Failed'}
                </span>
              </div>

              {/* Classification */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-1">Type</p>
                  <p className="text-sm font-medium text-gray-900">
                    {doc.document_type}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-1">Confidence</p>
                  <p className="text-sm font-medium text-gray-900">
                    {(doc.classification_confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Extracted Fields Summary */}
              {doc.extracted_fields && (
                <div className="border-t pt-4">
                  <p className="text-xs font-medium text-gray-600 mb-2">
                    Extracted Fields
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {doc.extracted_fields.map((field: any, i: number) => (
                      field.value && (
                        <span
                          key={i}
                          className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
                        >
                          {field.field.replace(/_/g, ' ')}
                        </span>
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Processing Info */}
              <div className="border-t pt-4 mt-4">
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <div className="flex items-center space-x-4">
                    <span>Chunks: {doc.chunk_count}</span>
                    <span>Time: {doc.processing_time_seconds}s</span>
                  </div>
                  {doc.firebase_enabled && (
                    <span className="flex items-center space-x-1 text-green-600">
                      <CheckCircle className="w-3 h-3" />
                      <span>Saved to Firebase</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
