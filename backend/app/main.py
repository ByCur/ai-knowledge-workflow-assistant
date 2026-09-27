from pathlib import Path
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from .document_service import extract_text
from .agent_service import run_agent

from contextlib import asynccontextmanager
from .schemas import DocumentDetailResponse, DocumentResponse
from .rag_service import generate_answer
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from .chunking_service import chunk_text
from .embedding_service import create_embeddings
from .config import settings
from .database import (
    check_database_connection,
    create_tables,
    get_db,
)
from .retrieval_service import (
    retrieve_relevant_chunks,
)
from .models import Document, DocumentChunk, Task
from .schemas import (
    ChunkResponse,
    DocumentDetailResponse,
    DocumentResponse,
    IndexDocumentResponse,
    AgentRequest,
    AgentResponse,
    SearchRequest,
    AskRequest,
    TaskCreate,
    TaskResponse,
    AskResponse,
    SearchResult,
)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="AI Knowledge & Workflow Assistant API",
    description=(
        "Backend API for an AI-powered "
        "knowledge and workflow platform."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI Knowledge & Workflow Assistant API"
    }


@app.get("/health")
def health():
    try:
        check_database_connection()

        return {
            "status": "ok",
            "backend": "running",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "error",
            "backend": "running",
            "database": "disconnected",
        }


@app.get(
    "/api/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(Document).order_by(
            Document.created_at.desc()
        )
    )

    return result.scalars().all()
@app.get(
    "/api/documents/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document

@app.get(
    "/api/documents/{document_id}/chunks",
    response_model=list[ChunkResponse],
)
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    result = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id
            == document_id
        )
        .order_by(
            DocumentChunk.chunk_index
        )
    )

    return result.scalars().all()

@app.delete(
    "/api/documents/{document_id}",
    status_code=200,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.file_path:
        file_path = Path(document.file_path)
        file_path.unlink(missing_ok=True)

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "id": document_id,
    }


@app.post(
    "/api/documents/upload",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File exceeds the 10 MB limit",
        )

    original_filename = file.filename or "document"

    safe_filename = (
        f"{uuid4()}_{Path(original_filename).name}"
    )

    file_path = UPLOAD_DIR / safe_filename
    file_path.write_bytes(contents)

    try:
        extracted_text = extract_text(
            file_path,
            file.content_type,
        )
    except Exception as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Could not process document: {error}",
        )

    document = Document(
    name=original_filename,
    description=description,
    original_filename=original_filename,
    content_type=file.content_type,
    file_path=str(file_path),
    file_size=len(contents),
    extracted_text=extracted_text,
    status="processing",
)

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = chunk_text(extracted_text)

    if chunks:
        embeddings = create_embeddings(chunks)

        for index, content in enumerate(chunks):
            db.add(
                DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                embedding=embeddings[index],
            )
        )

        document.status = "indexed"


    else:
        document.status = "processed"

    db.commit()
    db.refresh(document)

    return document

@app.post(
    "/api/documents/{document_id}/index",
    response_model=IndexDocumentResponse,
)
def index_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if not document.extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document has no extractable text",
        )

    chunks = chunk_text(
        document.extracted_text
    )

    embeddings = create_embeddings(
        chunks
    )

    db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_id
            == document_id
        )
    )

    for index, content in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
                embedding=embeddings[index],
            )
        )

    document.status = "indexed"

    db.commit()

    return {
        "document_id": document_id,
        "chunks_created": len(chunks),
        "status": "indexed",
    }

@app.post(
    "/api/search",
    response_model=list[SearchResult],
)
def semantic_search(
    search: SearchRequest,
    db: Session = Depends(get_db),
):
    return retrieve_relevant_chunks(
        db=db,
        query=search.query,
        limit=search.limit,
    )

@app.post(
    "/api/ask",
    response_model=AskResponse,
)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    sources = retrieve_relevant_chunks(
        db=db,
        query=request.question,
        limit=3,
    )

    if not sources:
        return {
            "answer": (
                "I don't have enough "
                "information in the uploaded "
                "documents to answer that."
            ),
            "sources": [],
        }

    answer = generate_answer(
        question=request.question,
        sources=sources,
    )

    return {
        "answer": answer,
        "sources": sources[:1],
    }

@app.post(
    "/api/tasks",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    existing_task = db.execute(
    select(Task).where(
        func.lower(Task.title)
        == task.title.strip().lower(),
        Task.status == "pending",
        Task.source_document_id
        == task.source_document_id,
        )
        ).scalar_one_or_none()

    if existing_task:
             raise HTTPException(
        status_code=409,
        detail="A pending task with this title already exists",
    )
    new_task = Task(
        title=task.title,
        description=task.description,
        source_document_id=task.source_document_id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.get(
    "/api/tasks",
    response_model=list[TaskResponse],
)
def list_tasks(
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(Task).order_by(
            Task.created_at.desc()
        )
    )

    return result.scalars().all()

@app.patch(
    "/api/tasks/{task_id}/complete",
    response_model=TaskResponse,
)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(
        Task,
        task_id,
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task.status = "completed"

    db.commit()
    db.refresh(task)

    return task

@app.delete(
    "/api/tasks/{task_id}",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(
        Task,
        task_id,
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully",
        "id": task_id,
    }

@app.post(
    "/api/agent",
    response_model=AgentResponse,
)
def execute_agent(
    request: AgentRequest,
    db: Session = Depends(get_db),
):
    return run_agent(
        db=db,
        instruction=request.instruction,
    )