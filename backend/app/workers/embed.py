import uuid

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from app.db.session import async_session_maker
from app.features.embeddings.models import Embedding, EmbedStatus
from app.features.embeddings.service import create_chunks, delete_chunks_for_node
from app.features.nodes.models import Node

model = SentenceTransformer("all-MiniLM-L6-v2")


async def embed_node(ctx: dict, node_id: str) -> None:
    async with async_session_maker() as db:
        try:
            # 1. Load the node
            result = await db.execute(
                select(Node).where(
                    Node.id == uuid.UUID(node_id),
                    Node.deleted_at.is_(None),
                )
            )
            node = result.scalar_one_or_none()
            if not node or not node.content:
                return

            # 2. Delete old chunks
            await delete_chunks_for_node(db, node.id)

            # 3. Create new chunks
            chunks = await create_chunks(db, node.id, node.content, node.version)

            # 4. Embed all chunks
            texts = [c.chunk_text for c in chunks]
            vectors = model.encode(texts).tolist()

            # 5. Update each chunk with its vector
            for chunk, vector in zip(chunks, vectors):
                chunk.embedding = vector
                chunk.embed_status = EmbedStatus.done

            await db.commit()
        except Exception:
            await db.rollback()
            # Optionally mark chunks as failed
            raise
