"""Vision Engine — orchestrates OCR, image analysis, and PDF processing.

Central coordinator for all vision operations. Integrates with
memory, RAG, and the workspace for a unified experience.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from config.logging import get_logger
from vision.image_analysis import ImageAnalyzer
from vision.ocr import OCREngine
from vision.pdf_ocr import PDFOCREngine
from vision.schemas import ImageAnalysis, OCRResult, VisionSettings

logger = get_logger(__name__)

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "application/pdf",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class VisionEngine:
    """Unified vision engine for OCR, analysis, and PDF processing."""

    def __init__(self, settings: VisionSettings | None = None) -> None:
        self._settings = settings or VisionSettings()
        self._ocr = OCREngine(preferred_provider=self._settings.ocr_provider)
        self._pdf = PDFOCREngine(ocr_engine=self._ocr, dpi=self._settings.dpi)
        self._analyzer = ImageAnalyzer(ocr_engine=self._ocr)
        self._stats = {"ocr_requests": 0, "pdf_requests": 0, "analyses": 0}

    @property
    def settings(self) -> VisionSettings:
        return self._settings

    def validate_file(self, file_path: Path) -> str | None:
        """Validate file for processing. Returns error message or None."""
        if not file_path.exists():
            return "File not found"
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE:
            return f"File too large ({size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE / 1024 / 1024}MB)"
        mime, _ = mimetypes.guess_type(str(file_path))
        if mime and mime not in ALLOWED_MIME_TYPES:
            return f"Unsupported file type: {mime}"
        return None

    def ocr(self, image_path: Path, language: str = "") -> OCRResult:
        """Run OCR on an image file."""
        self._stats["ocr_requests"] += 1
        lang = language or self._settings.language
        error = self.validate_file(image_path)
        if error:
            return OCRResult(text=f"[{error}]", provider="validation")
        return self._ocr.extract(image_path, lang)

    def ocr_from_bytes(
        self, data: bytes, filename: str = "image.png", language: str = ""
    ) -> OCRResult:
        """Run OCR on raw image bytes."""
        import tempfile

        self._stats["ocr_requests"] += 1
        lang = language or self._settings.language

        suffix = Path(filename).suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(data)

        try:
            return self._ocr.extract(tmp_path, lang)
        finally:
            tmp_path.unlink(missing_ok=True)

    def pdf_ocr(self, pdf_path: Path, language: str = "") -> OCRResult:
        """Run OCR on a PDF document."""
        self._stats["pdf_requests"] += 1
        lang = language or self._settings.language
        error = self.validate_file(pdf_path)
        if error:
            return OCRResult(text=f"[{error}]", provider="validation")
        return self._pdf.extract(pdf_path, lang)

    def analyze(self, image_path: Path, language: str = "") -> ImageAnalysis:
        """Analyze an image (classify type, extract text, entities)."""
        self._stats["analyses"] += 1
        lang = language or self._settings.language
        error = self.validate_file(image_path)
        if error:
            return ImageAnalysis(description=error)
        return self._analyzer.analyze(image_path, lang)

    def analyze_from_bytes(self, data: bytes, filename: str = "image.png") -> ImageAnalysis:
        """Analyze image from raw bytes."""
        import tempfile

        suffix = Path(filename).suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(data)

        try:
            return self.analyze(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    def get_status(self) -> dict[str, Any]:
        """Get vision engine status."""
        return {
            "available_providers": self._ocr.get_available_providers(),
            "stats": self._stats,
            "settings": {
                "ocr_provider": self._settings.ocr_provider.value,
                "language": self._settings.language,
                "dpi": self._settings.dpi,
                "max_file_size_mb": self._settings.max_file_size_mb,
            },
        }
