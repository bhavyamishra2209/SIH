'use client'

import { useState } from 'react'
import axios from 'axios'
import { Send, Bot, User, Loader2, FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  evidence?: any[]
}

export default function QueryInterface() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    const userMessage: Message = { role: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/query`, { query })
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        evidence: response.data.evidence,
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || 'Failed to process query'}`,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-t-lg">
        <div className="flex items-center space-x-3">
          <Bot className="w-6 h-6" />
          <div>
            <h3 className="font-semibold text-lg">AI Document Assistant</h3>
            <p className="text-sm text-blue-100">Ask me anything about your documents</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm text-center mt-2 max-w-md">
              Upload documents and start asking questions like:
            </p>
            <div className="mt-4 space-y-2 text-sm text-left">
              <p>• "What is the applicant's name?"</p>
              <p>• "When was this document filed?"</p>
              <p>• "Summarize the document"</p>
              <p>• "What is the purpose of this application?"</p>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex space-x-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user'
                    ? 'bg-blue-600'
                    : 'bg-gradient-to-r from-purple-600 to-blue-600'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-5 h-5 text-white" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`inline-block px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <ReactMarkdown className="prose prose-sm max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* Evidence */}
                  {message.evidence && message.evidence.length > 0 && (
                    <div className="mt-2 space-y-2">
                      <p className="text-xs text-gray-600 font-medium">Sources:</p>
                      {message.evidence.map((item: any, i: number) => (
                        <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                          <div className="flex items-start space-x-2">
                            <FileText className="w-4 h-4 text-gray-400 mt-0.5" />
                            <div className="flex-1">
                              <p className="text-xs font-medium text-gray-900">
                                {item.source_document}
                              </p>
                              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                {item.evidence_snippet}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                Confidence: {(item.confidence * 100).toFixed(1)}%
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-start">
            <div className="flex space-x-3 max-w-3xl">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            <Send className="w-5 h-5" />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}
