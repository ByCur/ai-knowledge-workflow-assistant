import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

const API_URL =
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'

type Document = {
  id: number
  name: string
  description: string
  status: string
  created_at: string
}

function App() {
  const [documents, setDocuments] =
    useState<Document[]>([])

  const [name, setName] = useState('')
  const [description, setDescription] =
    useState('')

  const [backendStatus, setBackendStatus] =
    useState('Checking backend...')

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
        setBackendStatus('Backend error')
      }
    } catch {
      setBackendStatus('Backend unavailable')
    }
  }

  async function loadDocuments() {
    const response = await fetch(
      `${API_URL}/api/documents`
    )

    const data = await response.json()

    setDocuments(data)
  }

  async function createDocument(
    event: FormEvent
  ) {
    event.preventDefault()

    if (!name.trim()) return

    await fetch(`${API_URL}/api/documents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name,
        description,
      }),
    })

    setName('')
    setDescription('')

    await loadDocuments()
  }

  useEffect(() => {
    checkBackend()
    loadDocuments()
  }, [])

  return (
    <main>
      <h1>AI Knowledge & Workflow Assistant</h1>

      <p>
        Upload, organize and interact with your
        knowledge using AI.
      </p>

      <p>
        <strong>Status:</strong>{' '}
        {backendStatus}
      </p>

      <hr />

      <h2>Add a document</h2>

      <form onSubmit={createDocument}>
        <input
          value={name}
          onChange={(event) =>
            setName(event.target.value)
          }
          placeholder="Document name"
        />

        <input
          value={description}
          onChange={(event) =>
            setDescription(event.target.value)
          }
          placeholder="Description"
        />

        <button type="submit">
          Add document
        </button>
      </form>

      <h2>Knowledge Base</h2>

      {documents.length === 0 ? (
        <p>No documents yet.</p>
      ) : (
        <ul>
          {documents.map((document) => (
            <li key={document.id}>
              <strong>{document.name}</strong>

              <p>{document.description}</p>

              <small>
                Status: {document.status}
              </small>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default App