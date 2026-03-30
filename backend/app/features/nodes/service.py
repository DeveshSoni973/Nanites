import uuid
import logging
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.features.nodes.models import Node, NodeType

logger = logging.getLogger(__name__)

_arq_pool = None


async def get_arq_pool():
    global _arq_pool
    if _arq_pool is None:
        url = settings.REDIS_URL.replace("redis://", "")
        host_port, db_num = url.rsplit("/", 1)
        host, port = host_port.split(":")
        _arq_pool = await create_pool(
            RedisSettings(host=host, port=int(port), database=int(db_num))
        )
    return _arq_pool


async def validate_parent(
    db: AsyncSession, user_id: uuid.UUID, parent_id: uuid.UUID | None
):
    if parent_id is None:
        return
    parent = await get_node(db, parent_id, user_id)
    if parent is None:
        raise ResourceNotFoundError("Parent does not exist")
    if parent.type != NodeType.folder:
        raise ValidationError("Cannot add a child folder or note to a note.")


async def create_node(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    type: NodeType,
    parent_id: uuid.UUID | None = None,
    content: str | None = None,
) -> Node:
    await validate_parent(db, user_id, parent_id)
    node = Node(
        user_id=user_id,
        title=title,
        type=type,
        parent_id=parent_id,
        content=content,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    if node.type == NodeType.note and node.content:
        try:
            logger.info(f"Enqueueing embed job for node {node.id}")
            pool = await get_arq_pool()
            job = await pool.enqueue_job("embed_node", str(node.id))
            logger.info(f"Enqueued embed job {job.job_id} for node {node.id}")
        except Exception as e:
            logger.error(f"Failed to enqueue embed job for node {node.id}: {e}", exc_info=True)
    return node


async def get_node(
    db: AsyncSession,
    node_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Node | None:
    result = await db.execute(
        select(Node).where(
            Node.id == node_id,
            Node.user_id == user_id,
            Node.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_nodes(
    db: AsyncSession,
    user_id: uuid.UUID,
    parent_id: uuid.UUID | None = None,
    type: NodeType | None = None,
    title: str | None = None,
    global_scan: bool = False,
) -> list[Node]:
    query = select(Node).where(
        Node.user_id == user_id,
        Node.deleted_at.is_(None),
    )
    if not global_scan:
        if parent_id is None:
            query = query.where(Node.parent_id.is_(None))
        else:
            query = query.where(Node.parent_id == parent_id)
    if type:
        query = query.where(Node.type == type)
    if title:
        query = query.where(Node.title.ilike(f"%{title}%"))
    query = query.order_by(Node.type.desc(), Node.title)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_node(
    db: AsyncSession,
    node_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str | None = None,
    content: str | None = None,
    parent_id: uuid.UUID | None = None,
) -> int:
    await validate_parent(db, user_id, parent_id)
    values = {}
    if title is not None:
        values["title"] = title
    if content is not None:
        values["content"] = content
        values["version"] = Node.version + 1
    if parent_id is not None:
        values["parent_id"] = parent_id
    if not values:
        return 0
    result = await db.execute(
        update(Node)
        .where(Node.id == node_id, Node.user_id == user_id, Node.deleted_at.is_(None))
        .values(**values)
    )
    await db.commit()
    if result.rowcount == 0:
        raise ResourceNotFoundError("Node not found")
    if content is not None:
        try:
            logger.info(f"Enqueueing embed job for updated node {node_id}")
            pool = await get_arq_pool()
            job = await pool.enqueue_job("embed_node", str(node_id))
            logger.info(f"Enqueued embed job {job.job_id} for node {node_id}")
        except Exception as e:
            logger.error(f"Failed to enqueue embed job for node {node_id}: {e}", exc_info=True)
    return result.rowcount


async def delete_node(
    db: AsyncSession,
    node_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    result = await db.execute(
        update(Node)
        .where(Node.id == node_id, Node.user_id == user_id, Node.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()
    if result.rowcount == 0:
        raise ResourceNotFoundError("Node not found")
    return result.rowcount


async def search_nodes_by_content(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
) -> list[Node]:
    result = await db.execute(
        select(Node).where(
            Node.user_id == user_id,
            Node.deleted_at.is_(None),
            Node.type == NodeType.note,
            Node.content.ilike(f"%{query}%"),
        )
    )
    return list(result.scalars().all())
