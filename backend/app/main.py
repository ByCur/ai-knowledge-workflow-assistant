from contextlib import asynccontextmanager

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
from .schemas import DocumentCreate, DocumentResponse


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


@app.post(
    "/api/documents",
    response_model=DocumentResponse,
    status_code=201,
)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
):
    new_document = Document(
        name=document.name,
        description=document.description,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document