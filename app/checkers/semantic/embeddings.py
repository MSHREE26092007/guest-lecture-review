"""Embedding utilities for the Semantic Quality Checker (module 5).

Lazy-loads sentence-transformers (all-mpnet-base-v2) only when enabled.
"""

import logging
from functools import lru_cache

from app.config import get_settings

log = logging.getLogger(__name__)
_model = None


def is_embeddings_available() -> bool:
    settings = get_settings()
    return settings.enable_embeddings


@lru_cache(maxsize=1)
def get_embedding_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _model = SentenceTransformer("all-mpnet-base-v2")
        log.info("Loaded sentence-transformers model: all-mpnet-base-v2")
    except Exception as exc:  # pragma: no cover - optional dep
        log.warning("sentence-transformers unavailable (%s); embeddings disabled", exc)
        _model = False
    return _model


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_text(text: str) -> list[float] | None:
    model = get_embedding_model()
    if not model:
        return None
    try:
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception as exc:
        log.warning("Embedding failed: %s", exc)
        return None