"""AI Coding Assistant API — code review, generation, analysis, search."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from coding_assistant.service import CodingAssistantService
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/coding", tags=["coding"])

_service = CodingAssistantService()


# ─── Schemas ─────────────────────────────────────────────────────────────────


class ReviewRequest(BaseModel):
    """Request to review source code."""

    source: str = Field(..., min_length=1, max_length=50000)
    file_path: str = Field("unnamed.py")


class ReviewResponse(BaseModel):
    """Response from code review."""

    file_path: str
    issues: list[dict] = Field(default_factory=list)
    score: float = 10.0
    passed: bool = True
    summary: str = ""


class GenerateTestsRequest(BaseModel):
    """Request to generate tests from source."""

    source: str = Field(..., min_length=1, max_length=50000)
    language: str = "python"


class GenerateTestsResponse(BaseModel):
    """Response from test generation."""

    content: str
    test_count: int = 0
    test_framework: str = "pytest"
    test_types: list[str] = Field(default_factory=list)
    success: bool = True


class GenerateDocsRequest(BaseModel):
    """Request to generate documentation from source."""

    source: str = Field(..., min_length=1, max_length=50000)
    language: str = "python"


class GenerateDocsResponse(BaseModel):
    """Response from documentation generation."""

    content: str
    language: str = "markdown"
    success: bool = True


class IndexWorkspaceResponse(BaseModel):
    """Response from workspace indexing."""

    files: int = 0
    symbols: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SearchCodeRequest(BaseModel):
    """Request to search indexed code."""

    query: str = Field(..., min_length=1, max_length=200)
    kind: str | None = None


class SearchCodeResponse(BaseModel):
    """Response from code search."""

    results: list[dict] = Field(default_factory=list)
    count: int = 0


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/review", response_model=ReviewResponse)
async def review_code(body: ReviewRequest) -> ReviewResponse:
    """Review source code and return issues."""
    result = await _service.review_code(body.source, body.file_path)
    return ReviewResponse(
        file_path=result.file_path,
        issues=[
            {
                "line": i.line,
                "column": i.column,
                "message": i.message,
                "severity": i.severity.value,
                "rule": i.rule,
                "suggestion": i.suggestion,
                "end_line": i.end_line,
            }
            for i in result.issues
        ],
        score=result.score,
        passed=result.passed,
    )


@router.post("/generate/tests", response_model=GenerateTestsResponse)
async def generate_tests(body: GenerateTestsRequest) -> GenerateTestsResponse:
    """Generate test code from source code."""
    result = await _service.generate_tests(body.source, body.language)
    return GenerateTestsResponse(
        content=result.content,
        test_count=result.test_count,
        test_framework=result.test_framework,
        test_types=result.test_types,
        success=result.success,
    )


@router.post("/generate/docs", response_model=GenerateDocsResponse)
async def generate_docs(body: GenerateDocsRequest) -> GenerateDocsResponse:
    """Generate documentation from source code."""
    result = await _service.generate_documentation(body.source, body.language)
    return GenerateDocsResponse(
        content=result.content,
        language=result.language,
        success=result.success,
    )


@router.post("/search", response_model=SearchCodeResponse)
async def search_code(body: SearchCodeRequest) -> SearchCodeResponse:
    """Search indexed code symbols."""
    results = await _service.search_code(body.query, body.kind)
    return SearchCodeResponse(results=results, count=len(results))


@router.post("/index", response_model=IndexWorkspaceResponse)
async def index_workspace() -> IndexWorkspaceResponse:
    """Index the workspace for code search."""
    result = await _service.index_workspace()
    return IndexWorkspaceResponse(
        files=result.files,
        symbols=[
            {
                "name": s.name,
                "kind": s.kind,
                "file": s.file_path,
                "line": s.line,
                "column": s.column,
                "parent": s.parent,
            }
            for s in result.symbols
        ],
        errors=result.errors,
    )


@router.get("/stats")
async def get_stats() -> dict:
    """Get coding assistant statistics."""
    return await _service.get_stats()
