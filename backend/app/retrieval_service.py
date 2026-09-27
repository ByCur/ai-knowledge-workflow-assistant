import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from .embedding_service import create_embeddings
from .models import Document, DocumentChunk


STOPWORDS = {
    "que",
    "qué",
    "es",
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "de",
    "del",
    "y",
    "en",
    "para",
    "por",
    "what",
    "is",
    "the",
    "a",
    "an",
    "of",
    "and",
    "in",
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(
            character
        )
    )

    text = text.lower()

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def compact_text(text: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        normalize_text(text),
    )


def lexical_score(
    query: str,
    content: str,
) -> float:
    normalized_query = normalize_text(
        query
    )

    normalized_content = normalize_text(
        content
    )

    query_words = [
        word
        for word in re.findall(
            r"\b\w+\b",
            normalized_query,
        )
        if (
            word not in STOPWORDS
            and len(word) > 2
        )
    ]

    if not query_words:
        return 0.0

    matches = sum(
        1
        for word in query_words
        if word in normalized_content
    )

    return matches / len(query_words)


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    limit: int = 3,
) -> list[dict]:

    query_embedding = create_embeddings(
        [query]
    )[0]

    distance = (
        DocumentChunk.embedding
        .cosine_distance(
            query_embedding
        )
    )

    # Retrieve more candidates than we finally need.
    candidate_limit = max(
        limit * 4,
        12,
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
            DocumentChunk.embedding.is_not(
                None
            )
        )
        .order_by(distance)
        .limit(candidate_limit)
    )

    candidates = []

    compact_query = compact_text(query)

    for (
        chunk,
        document_name,
        distance_value,
    ) in result:

        semantic_similarity = (
            1 - float(distance_value)
        )

        semantic_similarity = max(
            0.0,
            min(
                1.0,
                semantic_similarity,
            ),
        )

        lexical = lexical_score(
            query,
            chunk.content,
        )

        # Useful for extracted PDF text such as
        # "¿Qué esdocker?" where spaces may be lost.
        phrase_match = (
            1.0
            if compact_query
            and compact_query
            in compact_text(
                chunk.content
            )
            else 0.0
        )

        relevance_score = (
            semantic_similarity * 0.70
            + lexical * 0.20
            + phrase_match * 0.10
        )

        candidates.append(
            {
                "document_id":
                    chunk.document_id,
                "document_name":
                    document_name,
                "chunk_index":
                    chunk.chunk_index,
                "content":
                    chunk.content,

                # This is now the final ranking score.
                "similarity":
                    relevance_score,

                "_semantic_similarity":
                    semantic_similarity,
            }
        )

    candidates.sort(
        key=lambda item:
            item["similarity"],
        reverse=True,
    )

    results = candidates[:limit]

    # Internal field does not need to reach
    # the API/frontend.
    for item in results:
        item.pop(
            "_semantic_similarity",
            None,
        )

    return results