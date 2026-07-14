"""Vision & OCR schemas and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OCRProvider(str, Enum):
    """Supported OCR providers."""

    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"


class ImageType(str, Enum):
    """Recognized image content types."""

    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    DIAGRAM = "diagram"
    CODE = "code"
    ERROR = "error"
    PHOTO = "photo"
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """Text region bounding box."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class OCRRegion:
    """A detected text region with position and confidence."""

    text: str
    confidence: float
    bbox: BoundingBox | None = None
    language: str = "en"


@dataclass
class OCRResult:
    """Complete OCR extraction result."""

    text: str
    regions: list[OCRRegion] = field(default_factory=list)
    language: str = "en"
    confidence: float = 0.0
    provider: str = ""
    page_count: int = 1
    pages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageAnalysis:
    """Result of image understanding/analysis."""

    image_type: ImageType = ImageType.UNKNOWN
    description: str = ""
    extracted_text: str = ""
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionSettings:
    """Vision engine configuration."""

    ocr_provider: OCRProvider = OCRProvider.TESSERACT
    language: str = "eng"
    confidence_threshold: float = 0.3
    max_file_size_mb: float = 20.0
    supported_formats: list[str] = field(
        default_factory=lambda: ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp", "pdf"]
    )
    preprocessing: bool = True
    dpi: int = 300
