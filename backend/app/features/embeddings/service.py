import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from app.features.embeddings.models import Embedding, EmbedStatus
from app.features.nodes.models import Node, NodeType

_search_model = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(content: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    if not content or not content.strip():
        return []
    if len(content) < chunk_size:
        return [content]
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        if end >= len(content):
            chunks.append(content[start:])
            break
        for sep in ["\n\n", "\n", ". ", " "]:
            pos = content.rfind(sep, start, end)
            if pos > start:
                end = pos + len(sep)
                break
        chunks.append(content[start:end])
        start = end - overlap
    return chunks


async def delete_chunks_for_node(db: AsyncSession, node_id: uuid.UUID) -> None:
    await db.execute(delete(Embedding).where(Embedding.node_id == node_id))


async def create_chunks(
    db: AsyncSession,
    node_id: uuid.UUID,
    content: str,
    version: int,
) -> list[Embedding]:
    chunks = chunk_text(content)
    rows = []
    for i, text in enumerate(chunks):
        row = Embedding(
            node_id=node_id,
            chunk_index=i,
            chunk_text=text,
            node_version=version,
            embed_status=EmbedStatus.pending,
        )
        db.add(row)
        rows.append(row)
    await db.flush()
    return rows


async def semantic_search(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    limit: int = 10,
) -> list[dict]:
    query_embedding = _search_model.encode(query).tolist()
    result = await db.execute(
        select(Embedding, Node)
        .join(Node, Embedding.node_id == Node.id)
        .where(
            Node.user_id == user_id,
            Node.deleted_at.is_(None),
            Node.type == NodeType.note,
            Embedding.embed_status == EmbedStatus.done,
            Embedding.embedding.is_not(None),
        )
        .order_by(Embedding.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "node": row.Node,
            "snippet": row.Embedding.chunk_text,
        }
        for row in rows
    ]
