import {
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type FormEvent,
} from 'react'

import './App.css'

const API_URL =
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'

const MAX_FILE_SIZE = 10 * 1024 * 1024

type Document = {
  id: number
  name: string
  description: string
  original_filename: string | null
  content_type: string | null
  file_size: number | null
  status: string
  created_at: string
}

type DocumentDetail = Document & {
  extracted_text: string
}

type SearchSource = {
  document_id: number
  document_name: string
  chunk_index: number
  content: string
  similarity: number
}

type AskResponse = {
  answer: string
  sources: SearchSource[]
}

function formatFileSize(bytes: number | null) {
  if (!bytes) return 'Unknown size'

  if (bytes < 1024) {
    return `${bytes} B`
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function formatDate(date: string) {
  return new Date(date).toLocaleString()
}

function App() {
  const [documents, setDocuments] =
    useState<Document[]>([])

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null)

  const [description, setDescription] =
    useState('')

  const [backendStatus, setBackendStatus] =
    useState('Checking backend...')

  const [uploadStatus, setUploadStatus] =
    useState('')

  const [isUploading, setIsUploading] =
    useState(false)

  const [isDragging, setIsDragging] =
    useState(false)

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentDetail | null>(null)

  const [isLoadingDocument, setIsLoadingDocument] =
    useState(false)

  const fileInputRef =
    useRef<HTMLInputElement>(null)
  
  const [question, setQuestion] =
  useState('')

  const [answer, setAnswer] =
  useState('')

  const [answerSources, setAnswerSources] =
  useState<SearchSource[]>([])

  const [isAsking, setIsAsking] =
  useState(false)

  const [askError, setAskError] =
  useState('')

  async function checkBackend() {
    try {
      const response = await fetch(
        `${API_URL}/health`
      )

      const data = await response.json()

      if (
        data.status === 'ok' &&
        data.database === 'connected'
      ) {
        setBackendStatus(
          'Backend and PostgreSQL connected'
        )
      } else {
        setBackendStatus(
          'Backend or database error'
        )
      }
    } catch {
      setBackendStatus(
        'Backend unavailable'
      )
    }
  }

  async function loadDocuments() {
    try {
      const response = await fetch(
        `${API_URL}/api/documents`
      )

      if (!response.ok) {
        throw new Error(
          'Could not load documents'
        )
      }

      const data = await response.json()

      setDocuments(data)
    } catch {
      setUploadStatus(
        'Could not load documents'
      )
    }
  }
  async function openDocument(
  documentId: number
) {
  try {
    setIsLoadingDocument(true)

    const response = await fetch(
      `${API_URL}/api/documents/${documentId}`
    )

    if (!response.ok) {
      throw new Error(
        'Could not load document'
      )
    }

    const data =
      await response.json()

    setSelectedDocument(data)
  } catch {
    setUploadStatus(
      'Could not load document details'
    )
  } finally {
    setIsLoadingDocument(false)
  }
  }
  async function askQuestion(
  event: FormEvent
) {
  event.preventDefault()

  const cleanQuestion =
    question.trim()

  if (!cleanQuestion) {
    return
  }

  try {
    setIsAsking(true)
    setAskError('')
    setAnswer('')
    setAnswerSources([])

    const response = await fetch(
      `${API_URL}/api/ask`,
      {
        method: 'POST',

        headers: {
          'Content-Type':
            'application/json',
        },

        body: JSON.stringify({
          question: cleanQuestion,
          
        }),
      }
    )

    if (!response.ok) {
      throw new Error(
        'Could not generate an answer'
      )
    }

    const data: AskResponse =
      await response.json()

    setAnswer(data.answer)
    setAnswerSources(data.sources)

  } catch (error) {
    if (error instanceof Error) {
      setAskError(error.message)
    } else {
      setAskError(
        'Could not generate an answer'
      )
    }
  } finally {
    setIsAsking(false)
  }
}
  async function deleteDocument(
  documentId: number
) {
  const confirmed = window.confirm(
    'Are you sure you want to delete this document?'
  )

  if (!confirmed) return

  try {
    const response = await fetch(
      `${API_URL}/api/documents/${documentId}`,
      {
        method: 'DELETE',
      }
    )

    if (!response.ok) {
      throw new Error(
        'Could not delete document'
      )
    }

    if (
      selectedDocument?.id === documentId
    ) {
      setSelectedDocument(null)
    }

    setUploadStatus(
      'Document deleted successfully.'
    )

    await loadDocuments()
  } catch (error) {
    if (error instanceof Error) {
      setUploadStatus(error.message)
    } else {
      setUploadStatus(
        'Could not delete document'
      )
    }
  }
}

  function validateFile(file: File) {
    const allowedTypes = [
      'application/pdf',
      'text/plain',
    ]

    if (!allowedTypes.includes(file.type)) {
      setUploadStatus(
        'Only PDF and TXT files are supported.'
      )

      return false
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadStatus(
        'The file exceeds the 10 MB limit.'
      )

      return false
    }

    setUploadStatus('')
    return true
  }

  function chooseFile(file: File) {
    if (!validateFile(file)) {
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
  }

  function handleFileInput(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0]

    if (file) {
      chooseFile(file)
    }
  }

  function handleDragOver(
    event: DragEvent<HTMLDivElement>
  ) {
    event.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave(
    event: DragEvent<HTMLDivElement>
  ) {
    event.preventDefault()
    setIsDragging(false)
  }

  function handleDrop(
    event: DragEvent<HTMLDivElement>
  ) {
    event.preventDefault()
    setIsDragging(false)

    const file =
      event.dataTransfer.files?.[0]

    if (file) {
      chooseFile(file)
    }
  }

  async function uploadDocument(
    event: FormEvent
  ) {
    event.preventDefault()

    if (!selectedFile) {
      setUploadStatus(
        'Select a document first.'
      )
      return
    }

    const formData = new FormData()

    formData.append(
      'file',
      selectedFile
    )

    formData.append(
      'description',
      description
    )

    try {
      setIsUploading(true)
      setUploadStatus('Uploading...')

      const response = await fetch(
        `${API_URL}/api/documents/upload`,
        {
          method: 'POST',
          body: formData,
        }
      )

      if (!response.ok) {
        const error =
          await response.json()

        throw new Error(
          error.detail ||
            'Upload failed'
        )
      }

      setUploadStatus(
        'Document processed successfully.'
      )

      setSelectedFile(null)
      setDescription('')

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      await loadDocuments()
    } catch (error) {
      if (error instanceof Error) {
        setUploadStatus(error.message)
      } else {
        setUploadStatus(
          'Upload failed'
        )
      }
    } finally {
      setIsUploading(false)
    }
  }

  useEffect(() => {
    checkBackend()
    loadDocuments()
  }, [])

  return (
    <main className="page">
      <section className="hero">
        <div>
          <span className="badge">
            AI-Powered Knowledge Platform
          </span>

          <h1>
            AI Knowledge & Workflow Assistant
          </h1>

          <p>
            Upload documents, build your
            knowledge base and prepare your
            information for AI-powered search,
            RAG and intelligent workflows.
          </p>
        </div>

        <div className="architecture">
          <strong>
            Current architecture
          </strong>

          <span>React + TypeScript</span>
          <span>FastAPI + Python</span>
          <span>PostgreSQL</span>
          <span>Docker</span>
        </div>
      </section>

      <section className="statusBar">
        <span
          className={
            backendStatus.includes(
              'connected'
            )
              ? 'status success'
              : 'status error'
          }
        >
          {backendStatus}
        </span>

        <span>
          {documents.length}{' '}
          {documents.length === 1
            ? 'document'
            : 'documents'}{' '}
          in knowledge base
        </span>
      </section>

      <section className="panel">
        <div className="sectionHeader">
          <div>
            <h2>Upload document</h2>

            <p>
              Add a PDF or TXT document to
              your knowledge base.
            </p>
          </div>
        </div>

        <form
          onSubmit={uploadDocument}
          className="uploadForm"
        >
          <div
            className={`dropZone ${
              isDragging
                ? 'dragging'
                : ''
            }`}
            onDragOver={handleDragOver}
            onDragLeave={
              handleDragLeave
            }
            onDrop={handleDrop}
            onClick={() =>
              fileInputRef.current?.click()
            }
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={
                handleFileInput
              }
              hidden
            />

            {selectedFile ? (
              <>
                <div className="fileIcon">
                  📄
                </div>

                <strong>
                  {selectedFile.name}
                </strong>

                <span>
                  {formatFileSize(
                    selectedFile.size
                  )}
                </span>

                <span>
                  {selectedFile.type}
                </span>
              </>
            ) : (
              <>
                <div className="uploadIcon">
                  ↑
                </div>

                <strong>
                  Drag & drop a document
                </strong>

                <span>
                  or click to select a file
                </span>

                <small>
                  PDF or TXT · Maximum 10 MB
                </small>
              </>
            )}
          </div>

          <textarea
            value={description}
            onChange={(event) =>
              setDescription(
                event.target.value
              )
            }
            placeholder="Optional description, e.g. Artificial Intelligence course notes"
          />

          <button
            type="submit"
            disabled={
              !selectedFile ||
              isUploading
            }
          >
            {isUploading
              ? 'Processing document...'
              : 'Upload document'}
          </button>

          {uploadStatus && (
            <p className="uploadStatus">
              {uploadStatus}
            </p>
          )}
        </form>
      </section>

      <section className="aiSection">
  <div className="sectionHeader">
    <div>
      <span className="aiBadge">
        RAG Assistant
      </span>

      <h2>
        Ask your Knowledge Base
      </h2>

      <p>
        Ask questions about your uploaded
        documents. The assistant retrieves
        relevant information and answers
        using local AI.
      </p>
    </div>
  </div>

  <form
    className="askForm"
    onSubmit={askQuestion}
  >
    <textarea
      value={question}
      onChange={(event) =>
        setQuestion(
          event.target.value
        )
      }
      placeholder="Ask something about your documents..."
    />

    <button
      type="submit"
      disabled={
        isAsking ||
        !question.trim()
      }
    >
      {isAsking
        ? 'Thinking...'
        : 'Ask AI'}
    </button>
  </form>

  {askError && (
    <div className="aiError">
      {askError}
    </div>
  )}

  {isAsking && (
    <div className="thinkingBox">
      <div className="thinkingDot" />

      <div>
        <strong>
          Searching knowledge base...
        </strong>

        <p>
          Retrieving relevant chunks and
          generating an answer locally.
        </p>
      </div>
    </div>
  )}

  {answer && (
    <div className="answerCard">
      <div className="answerHeader">
        <span className="aiAvatar">
          AI
        </span>

        <div>
          <strong>
            Knowledge Assistant
          </strong>

          <span>
            Local RAG response
          </span>
        </div>
      </div>

      <div className="answerText">
        {answer}
      </div>

      {answerSources.length > 0 && (
        <div className="sourcesSection">
          <h3>
            Best Source
          </h3>

          <div className="sourceGrid">
            {answerSources.map(
              (source, index) => (
                <button
                  type="button"
                  className="sourceCard"
                  key={
                    `${source.document_id}-${source.chunk_index}`
                  }
                  onClick={() =>
                    openDocument(
                      source.document_id
                    )
                  }
                >
                  <div className="sourceTop">
                    <span>
                      Source {index + 1}
                    </span>

                    <span>
                      {(
                        source.similarity *
                        100
                      ).toFixed(1)}
                      % match
                    </span>
                  </div>

                  <strong>
                    {source.document_name}
                  </strong>

                  <p>
                    {source.content}
                  </p>

                  <small>
                    Chunk{' '}
                    {source.chunk_index}
                  </small>
                </button>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )}
        </section>

      <section className="knowledgeSection">
        <div className="sectionHeader">
          <div>
            <h2>Knowledge Base</h2>

            <p>
              Documents currently available
              in the assistant.
            </p>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="emptyState">
            <h3>
              No documents yet
            </h3>

            <p>
              Upload your first PDF or TXT
              document.
            </p>
          </div>
        ) : (
          <div className="documentGrid">
            {documents.map(
              (document) => (
                <article
                  className="documentCard"
                  key={document.id}
                  onClick={() =>
                    openDocument(document.id)
                  }
                >
                  <div className="documentTop">
                    <div className="documentIcon">
                      📄
                    </div>

                    <span
                      className={`documentStatus ${document.status}`}
                    >
                      {document.status}
                    </span>
                  </div>

                  <h3>
                    {document.name}
                  </h3>

                  <p>
                    {document.description ||
                      'No description provided.'}
                  </p>

                  <div className="metadata">
                    
                    <span>
                      <strong>
                        Type
                      </strong>
                      {document.content_type ||
                        'Unknown'}
                    </span>

                    <span>
                      <strong>
                        Size
                      </strong>
                      {formatFileSize(
                        document.file_size
                      )}
                    </span>

                    <span>
                      <strong>
                        Added
                      </strong>
                      {formatDate(
                        document.created_at
                      )}
                    </span>
                  </div>

                  <button
                  className="deleteButton"
                    onClick={(event) => {
                    event.stopPropagation()
                    deleteDocument(document.id)
                  }}
  >
                Delete
                </button>
                </article>
              )
            )}
          </div>
        )}
      </section>
      

        {selectedDocument && (
          <section className="documentDetail">
            ...
          </section>
        )}

        {isLoadingDocument && (
          <p className="loadingText">
          Loading document...
         </p>
       )}
    </main>
  )
}

export default App