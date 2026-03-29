import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import get_current_user
from app.features.embeddings.service import semantic_search
from app.features.nodes.models import NodeType
from app.features.nodes.schema import (
    NodeCreate,
    NodeResponse,
    NodeUpdate,
    SearchResponse,
)
from app.features.nodes.service import (
    create_node,
    delete_node,
    get_node,
    get_nodes,
    search_nodes_by_content,
    update_node,
)
from app.features.users.models import User

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NodeResponse)
async def create(
    payload: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_node(
        db,
        user_id=current_user.id,
        title=payload.title,
        type=payload.type,
        parent_id=payload.parent_id,
        content=payload.content,
    )


@router.get("", response_model=list[NodeResponse])
async def browse(
    parent_id: uuid.UUID | None = None,
    type: NodeType | None = None,
    title: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_nodes(db, current_user.id, parent_id, type, title)


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text_results = await search_nodes_by_content(db, current_user.id, q)

    semantic_hits = await semantic_search(db, current_user.id, q)
    semantic_results = [
        NodeResponse(
            id=hit["node"].id,
            parent_id=hit["node"].parent_id,
            type=hit["node"].type,
            title=hit["node"].title,
            snippet=hit["snippet"],
            created_at=hit["node"].created_at,
            updated_at=hit["node"].updated_at,
        )
        for hit in semantic_hits
    ]

    return {
        "text_results": text_results,
        "semantic_results": semantic_results,
    }


@router.get("/{node_id}", response_model=NodeResponse)
async def get_one(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    node = await get_node(db, node_id, current_user.id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.put("/{node_id}")
async def update(
    node_id: uuid.UUID,
    payload: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await update_node(
        db,
        node_id,
        current_user.id,
        title=payload.title,
        content=payload.content,
        parent_id=payload.parent_id,
    )
    if rows == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "updated"}


@router.delete("/{node_id}")
async def delete(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await delete_node(db, node_id, current_user.id)
    if rows == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "deleted"}
