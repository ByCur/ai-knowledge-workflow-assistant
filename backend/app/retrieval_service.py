from sqlalchemy import select
from sqlalchemy.orm import Session

from .embedding_service import create_embeddings
from .models import Document, DocumentChunk


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    limit: int = 5,
) -> list[dict]:

    query_embedding = create_embeddings(
        [query]
    )[0]

    distance = (
        DocumentChunk.embedding
        .cosine_distance(query_embedding)
    )

    result = db.execute(
        select(
            DocumentChunk,
            Document.name,
            distance.label("distance"),
        )
        .join(
            Document,
            Document.id
            == DocumentChunk.document_id,
        )
        .where(
            DocumentChunk.embedding.is_not(None)
        )
        .order_by(distance)
        .limit(limit)
    )

    results = []

    for (
        chunk,
        document_name,
        distance_value,
    ) in result:

        similarity = 1 - float(
            distance_value
        )

        similarity = max(
            0.0,
            min(1.0, similarity),
        )

        results.append(
            {
                "document_id":
                    chunk.document_id,
                "document_name":
                    document_name,
                "chunk_index":
                    chunk.chunk_index,
                "content":
                    chunk.content,
                "similarity":
                    similarity,
            }
        )

    return results