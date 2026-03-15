import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.nodes.models import Node, NodeType


async def create_node(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    type: NodeType,
    parent_id: uuid.UUID | None = None,
    content: str | None = None,
) -> Node:
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
) -> list[Node]:
    query = select(Node).where(
        Node.user_id == user_id,
        Node.deleted_at.is_(None),
        Node.parent_id == parent_id,
    )
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
