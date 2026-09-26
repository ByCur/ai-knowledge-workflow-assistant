from functools import lru_cache

from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        settings.embedding_model
    )


def create_embeddings(
    texts: list[str],
) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    return embeddings.tolist()