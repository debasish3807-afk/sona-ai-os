"""Vision & OCR API — endpoints for image understanding.

POST /vision/ocr — Extract text from image
POST /vision/analyze — Analyze image content
POST /vision/pdf — OCR a PDF document
GET /vision/status — Engine availability
GET /vision/settings — Configuration
PATCH /vision/settings — Update settings
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config.logging import get_logger
from vision.engine import VisionEngine

logger = get_logger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"])

_engine = VisionEngine()

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB


class OCRRequest(BaseModel):
    """OCR request with base64 image."""

    image_base64: str = Field(..., description="Base64-encoded image")
    filename: str = "image.png"
    language: str = ""


class AnalyzeRequest(BaseModel):
    """Image analysis request."""

    image_base64: str = Field(..., description="Base64-encoded image")
    filename: str = "image.png"


class PDFRequest(BaseModel):
    """PDF OCR request."""

    pdf_base64: str = Field(..., description="Base64-encoded PDF")
    language: str = ""


class VisionSettingsUpdate(BaseModel):
    """Vision settings update."""

    language: str = ""
    ocr_provider: str = ""
    confidence_threshold: float | None = None
    dpi: int | None = None


@router.post("/ocr")
async def vision_ocr(request: OCRRequest) -> dict[str, Any]:
    """Extract text from an image using OCR."""
    try:
        data = base64.b64decode(request.image_base64)
    except Exception:
        return {"error": "Invalid base64 data"}

    if len(data) > MAX_UPLOAD_SIZE:
        return {"error": "File too large"}

    result = _engine.ocr_from_bytes(data, request.filename, request.language)
    return {
        "text": result.text,
        "confidence": result.confidence,
        "provider": result.provider,
        "region_count": len(result.regions),
        "language": result.language,
        "regions": [
            {
                "text": r.text,
                "confidence": r.confidence,
                "bbox": {"x": r.bbox.x, "y": r.bbox.y, "w": r.bbox.width, "h": r.bbox.height}
                if r.bbox
                else None,
            }
            for r in result.regions[:50]  # Limit regions in response
        ],
    }


@router.post("/analyze")
async def vision_analyze(request: AnalyzeRequest) -> dict[str, Any]:
    """Analyze image content — classify type, extract text, entities."""
    try:
        data = base64.b64decode(request.image_base64)
    except Exception:
        return {"error": "Invalid base64 data"}

    if len(data) > MAX_UPLOAD_SIZE:
        return {"error": "File too large"}

    result = _engine.analyze_from_bytes(data, request.filename)
    return {
        "image_type": result.image_type.value,
        "description": result.description,
        "extracted_text": result.extracted_text,
        "entities": result.entities,
        "confidence": result.confidence,
        "metadata": result.metadata,
    }


@router.post("/pdf")
async def vision_pdf(request: PDFRequest) -> dict[str, Any]:
    """Extract text from a scanned PDF."""
    try:
        data = base64.b64decode(request.pdf_base64)
    except Exception:
        return {"error": "Invalid base64 data"}

    if len(data) > MAX_UPLOAD_SIZE:
        return {"error": "File too large"}

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(data)

    try:
        result = _engine.pdf_ocr(tmp_path, request.language)
        return {
            "text": result.text,
            "page_count": result.page_count,
            "pages": result.pages,
            "confidence": result.confidence,
            "provider": result.provider,
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/status")
async def vision_status() -> dict[str, Any]:
    """Get vision engine status and available providers."""
    return _engine.get_status()


@router.get("/settings")
async def get_vision_settings() -> dict[str, Any]:
    """Get current vision settings."""
    s = _engine.settings
    return {
        "ocr_provider": s.ocr_provider.value,
        "language": s.language,
        "confidence_threshold": s.confidence_threshold,
        "dpi": s.dpi,
        "max_file_size_mb": s.max_file_size_mb,
        "supported_formats": s.supported_formats,
    }


@router.patch("/settings")
async def update_vision_settings(update: VisionSettingsUpdate) -> dict[str, Any]:
    """Update vision settings."""
    s = _engine.settings
    if update.language:
        s.language = update.language
    if update.confidence_threshold is not None:
        s.confidence_threshold = update.confidence_threshold
    if update.dpi is not None:
        s.dpi = update.dpi
    return {"updated": True}
