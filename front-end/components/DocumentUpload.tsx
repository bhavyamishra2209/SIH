'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface DocumentUploadProps {
  onDocumentUploaded: (document: any) => void
}

export default function DocumentUpload({ onDocumentUploaded }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      
      // ISSUE 4 FIX: Append all files (backend now accepts multiple)
      acceptedFiles.forEach((file) => {
        formData.append('files', file)
      })

      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      // Backend now returns array of results
      setResult(response.data)
      
      // Add all documents to parent state
      if (Array.isArray(response.data)) {
        response.data.forEach((doc: any) => {
          if (doc.status === 'success') {
            onDocumentUploaded(doc)
          }
        })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload documents')
    } finally {
      setUploading(false)
    }
  }, [onDocumentUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,  // ISSUE 4 FIX: Allow multiple files
  })

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          {uploading ? (
            <>
              <Loader2 className="w-16 h-16 text-blue-600 animate-spin" />
              <p className="text-lg font-medium text-gray-900">Processing document...</p>
              <p className="text-sm text-gray-600">This may take a few seconds</p>
            </>
          ) : (
            <>
              <Upload className="w-16 h-16 text-gray-400" />
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive ? 'Drop the file here' : 'Drag & drop a document'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  or click to browse
                </p>
              </div>
              <p className="text-xs text-gray-500">
                Supports: PDF, Images (PNG, JPG), DOCX, TXT • Drop multiple files at once!
              </p>
            </>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-900">Upload Failed</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && (
        <div className="space-y-4">
          {Array.isArray(result) ? (
            // Multiple documents
            result.map((doc: any, index: number) => (
              <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden">
                {/* Header */}
                <div className={`${doc.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border-b px-6 py-4`}>
                  <div className="flex items-center space-x-3">
                    {doc.status === 'success' ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-red-600" />
                    )}
                    <div>
                      <h3 className={`text-lg font-semibold ${doc.status === 'success' ? 'text-green-900' : 'text-red-900'}`}>
                        {doc.filename || `Document ${index + 1}`}
                      </h3>
                      <p className={`text-sm mt-1 ${doc.status === 'success' ? 'text-green-700' : 'text-red-700'}`}>
                        {doc.message}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Details (only for successful uploads) */}
                {doc.status === 'success' && (
                  <div className="p-6 space-y-6">
                    {/* Classification */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Classification</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1">Document Type</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {doc.document_type}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1">Confidence</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {(doc.classification_confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Extracted Fields */}
                    {doc.extracted_fields && doc.extracted_fields.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Extracted Fields</h4>
                        <div className="space-y-2">
                          {doc.extracted_fields.map((field: any, fieldIndex: number) => (
                            field.value && (
                              <div key={fieldIndex} className="bg-gray-50 rounded-lg p-4">
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <p className="text-xs font-medium text-gray-600">
                                      {field.field.replace(/_/g, ' ').toUpperCase()}
                                    </p>
                                    <p className="text-sm text-gray-900 mt-1">
                                      {field.value}
                                    </p>
                                  </div>
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    field.confidence > 0.7
                                      ? 'bg-green-100 text-green-800'
                                      : field.confidence > 0.4
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : 'bg-red-100 text-red-800'
                                  }`}>
                                    {(field.confidence * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                            )
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Processing Info</h4>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1">Chunks</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {doc.chunk_count}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1">Processing Time</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {doc.processing_time_seconds}s
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-xs text-gray-600 mb-1">Firebase</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {doc.firebase_enabled ? '✓ Yes' : '✗ No'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            // Single document (backward compatibility)
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Header */}
          <div className="bg-green-50 border-b border-green-200 px-6 py-4">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Document Processed Successfully!
                </h3>
                <p className="text-sm text-green-700 mt-1">
                  {result.message}
                </p>
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="p-6 space-y-6">
            {/* Classification */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Classification</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Document Type</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {result.document_type}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Confidence</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {(result.classification_confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Extracted Fields */}
            {result.extracted_fields && result.extracted_fields.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Extracted Fields</h4>
                <div className="space-y-2">
                  {result.extracted_fields.map((field: any, index: number) => (
                    field.value && (
                      <div key={index} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-600">
                              {field.field.replace(/_/g, ' ').toUpperCase()}
                            </p>
                            <p className="text-sm text-gray-900 mt-1">
                              {field.value}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            field.confidence > 0.7
                              ? 'bg-green-100 text-green-800'
                              : field.confidence > 0.4
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {(field.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Processing Info</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Chunks</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {result.chunk_count}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Processing Time</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {result.processing_time_seconds}s
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Firebase</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {result.firebase_enabled ? '✓ Yes' : '✗ No'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
