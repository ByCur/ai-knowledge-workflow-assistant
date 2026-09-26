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

from contextlib import asynccontextmanager
from .schemas import DocumentDetailResponse, DocumentResponse

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import (
    check_database_connection,
    create_tables,
    get_db,
)
from .models import Document
from .schemas import DocumentResponse

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
        status="processed",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document