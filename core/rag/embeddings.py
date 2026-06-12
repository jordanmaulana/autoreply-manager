from functools import lru_cache

from django.conf import settings

BATCH_SIZE = 100


@lru_cache(maxsize=1)
def get_client():
    from openai import OpenAI

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured.")
    return OpenAI(api_key=settings.OPENAI_API_KEY, max_retries=3)


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = get_client().embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL, input=batch
        )
        vectors.extend(item.embedding for item in response.data)
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
