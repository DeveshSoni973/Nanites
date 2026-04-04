import logging
import os
import threading

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MAX_THREADS = int(os.environ.get("TORCH_NUM_THREADS", "1")) # Reduced to 1 to prevent system freezes
torch.set_num_threads(MAX_THREADS)

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2 (device: cpu)")
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        _model.eval()
        logger.info(f"Model loaded (torch threads={torch.get_num_threads()})")
    return _model


def encode_texts(texts: list[str] | str, batch_size: int = 8) -> list:
    """Encode texts with proper memory management."""
    model = get_model()
    count = len(texts) if isinstance(texts, list) else 1
    logger.info(f"Encoding {count} text(s), batch_size={batch_size}")
    with torch.no_grad():
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()
    logger.info("Encoding complete")
    return vectors
