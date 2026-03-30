import gc
import uuid
import logging
import time

from sqlalchemy import select

from app.db.session import async_session_maker
from app.features.embeddings.models import Embedding, EmbedStatus
from app.features.embeddings.service import create_chunks, delete_chunks_for_node
from app.features.nodes.models import Node
from app.ml.model import encode_texts

logger = logging.getLogger(__name__)


async def embed_node(ctx: dict, node_id: str) -> None:
    job_start = time.perf_counter()
    logger.info(f"[embed] START node_id={node_id}")

    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(Node).where(
                    Node.id == uuid.UUID(node_id),
                    Node.deleted_at.is_(None),
                )
            )
            node = result.scalar_one_or_none()
            if not node or not node.content:
                logger.warning(f"[embed] SKIP node_id={node_id} — not found or empty content")
                return

            logger.info(
                f"[embed] node_id={node_id} title={node.title!r} "
                f"content_len={len(node.content)} version={node.version}"
            )

            await delete_chunks_for_node(db, node.id)

            chunks = await create_chunks(db, node.id, node.content, node.version)
            logger.info(f"[embed] node_id={node_id} created {len(chunks)} chunks")

            texts = [c.chunk_text for c in chunks]

            encode_start = time.perf_counter()
            vectors = encode_texts(texts)
            encode_ms = (time.perf_counter() - encode_start) * 1000
            logger.info(f"[embed] node_id={node_id} encoded {len(texts)} chunks in {encode_ms:.0f}ms")

            for chunk, vector in zip(chunks, vectors):
                chunk.embedding = vector
                chunk.embed_status = EmbedStatus.done

            await db.commit()
            gc.collect()

            total_ms = (time.perf_counter() - job_start) * 1000
            logger.info(f"[embed] DONE node_id={node_id} chunks={len(chunks)} total={total_ms:.0f}ms")
        except Exception as e:
            logger.error(f"[embed] FAIL node_id={node_id}: {e}", exc_info=True)
            await db.rollback()
            raise
