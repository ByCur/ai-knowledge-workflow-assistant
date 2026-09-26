from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector


from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    extracted_text: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(384),
    nullable=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )