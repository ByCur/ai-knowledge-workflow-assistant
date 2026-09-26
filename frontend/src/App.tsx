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

  const fileInputRef =
    useRef<HTMLInputElement>(null)

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
                </article>
              )
            )}
          </div>
        )}
      </section>
    </main>
  )
}

export default App