import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.features.nodes.models import NodeType


class NodeCreate(BaseModel):
    title: str
    type: NodeType
    parent_id: Optional[uuid.UUID] = None
    content: Optional[str] = None


class NodeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class NodeResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    type: NodeType
    title: str
    snippet: str | None = None  # null for browse, populated for semantic search
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    text_results: list[NodeResponse]
    semantic_results: list[NodeResponse]
