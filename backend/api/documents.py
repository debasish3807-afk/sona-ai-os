"""Document & memory API endpoints for the Knowledge Engine.

Endpoints:
    POST /documents/upload  — Ingest a document into knowledge base
    POST /documents/index   — Index raw text content
    GET  /documents/search  — Search documents (hybrid)
    GET  /memory/search     — Search memories
    GET  /memory/context    — Build AI context from knowledge
    DELETE /documents/{id}  — Delete a document
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.logging import get_logger
from rag.engine import get_rag_engine, initialize_rag

logger = get_logger(__name__)
router = APIRouter(tags=["knowledge"])


# --- Schemas ---


class DocumentUploadRequest(BaseModel):
    """POST /documents/upload request."""

    content: str = Field(..., min_length=1)
    title: str = Field(default="")
    source: str = Field(default="")
    doc_type: str = Field(default="text")
    tags: list[str] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    """POST /documents/upload response."""

    success: bool = True
    doc_id: str
    title: str
    chunks_created: int
    token_count: int


class DocumentSearchRequest(BaseModel):
    """GET /documents/search query params."""

    query: str
    top_k: int = 5
    min_score: float = 0.1


class SearchResultSchema(BaseModel):
    """A single search result."""

    content: str
    score: float
    source: str = ""
    doc_id: str = ""
    match_type: str = ""


class SearchResponse(BaseModel):
    """Search response."""

    success: bool = True
    results: list[SearchResultSchema]
    total: int


class ContextResponse(BaseModel):
    """GET /memory/context response."""

    success: bool = True
    context: str
    sources_used: int


# --- Endpoints ---


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(request: DocumentUploadRequest) -> DocumentUploadResponse:
    """Ingest a document into the knowledge base.

    The document is chunked, embedded, and stored for semantic
    and keyword retrieval.
    """
    engine = get_rag_engine()
    if not engine.is_initialized:
        await initialize_rag()

    doc = await engine.ingest_document(
        content=request.content,
        title=request.title,
        source=request.source,
        doc_type=request.doc_type,
        tags=request.tags,
    )

    return DocumentUploadResponse(
        doc_id=doc.doc_id,
        title=doc.title,
        chunks_created=doc.chunk_count,
        token_count=doc.token_count,
    )


@router.post("/documents/index", response_model=DocumentUploadResponse)
async def index_document(request: DocumentUploadRequest) -> DocumentUploadResponse:
    """Index raw text content (alias for upload)."""
    return await upload_document(request)


@router.get("/documents/search", response_model=SearchResponse)
async def search_documents(query: str, top_k: int = 5, min_score: float = 0.1) -> SearchResponse:
    """Search the knowledge base using hybrid retrieval.

    Combines semantic (embedding) and keyword (FTS) search
    for best results.
    """
    engine = get_rag_engine()
    if not engine.is_initialized:
        await initialize_rag()

    results = await engine.search(query, top_k=top_k, min_score=min_score)

    return SearchResponse(
        results=[
            SearchResultSchema(
                content=r.content[:1000],
                score=round(r.score, 4),
                source=r.source,
                doc_id=r.doc_id,
                match_type=r.match_type,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/memory/search", response_model=SearchResponse)
async def search_memory(query: str, top_k: int = 5, min_score: float = 0.1) -> SearchResponse:
    """Search across all memories (conversations, notes, etc.)."""
    engine = get_rag_engine()
    if not engine.is_initialized:
        await initialize_rag()

    results = await engine.search(query, top_k=top_k, min_score=min_score)
    return SearchResponse(
        results=[
            SearchResultSchema(
                content=r.content[:1000],
                score=round(r.score, 4),
                source=r.source,
                doc_id=r.doc_id,
                match_type=r.match_type,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/memory/context", response_model=ContextResponse)
async def get_memory_context(query: str, max_tokens: int = 2000, top_k: int = 5) -> ContextResponse:
    """Build AI context from the knowledge base.

    Retrieves the most relevant documents and memories, formats
    them as context for injection into an AI prompt.
    """
    engine = get_rag_engine()
    if not engine.is_initialized:
        await initialize_rag()

    context = await engine.build_context(query, max_tokens=max_tokens, top_k=top_k)
    results = await engine.search(query, top_k=top_k)

    return ContextResponse(
        context=context,
        sources_used=len(results),
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict[str, Any]:
    """Delete a document from the knowledge base."""
    engine = get_rag_engine()
    if not engine.is_initialized:
        await initialize_rag()

    deleted = await engine.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return {"success": True, "doc_id": doc_id, "deleted": True}
