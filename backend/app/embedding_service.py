from functools import lru_cache

from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache
def get_local_embedding_model():
    return SentenceTransformer(
        settings.embedding_model
    )


def create_embeddings(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    if not texts:
        return []

    provider = (
        settings.embedding_provider
        .strip()
        .lower()
    )

    if provider == "local":
        model = get_local_embedding_model()

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required "
                "for Gemini embeddings"
            )

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        result = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=(
                    settings.embedding_dimensions
                ),
            ),
        )

        return [
            embedding.values
            for embedding in result.embeddings
        ]

    raise RuntimeError(
        f"Unsupported embedding provider: "
        f"{settings.embedding_provider}"
    )