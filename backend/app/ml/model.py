import logging
import threading

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _model.eval()
        logger.info("Model loaded successfully")
    return _model


def encode_texts(texts: list[str] | str, batch_size: int = 8) -> list:
    """Encode texts with proper memory management."""
    model = get_model()
    logger.info(f"Encoding {len(texts) if isinstance(texts, list) else 1} text(s), batch_size={batch_size}")
    with torch.no_grad():
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()
    logger.info("Encoding complete")
    return vectors
