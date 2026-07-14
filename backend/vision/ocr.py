"""OCR Engine — local text extraction from images.

Supports Tesseract, EasyOCR, and PaddleOCR with automatic fallback.
All processing is local — no cloud APIs, privacy-preserving.
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from config.logging import get_logger
from vision.schemas import BoundingBox, OCRProvider, OCRRegion, OCRResult

logger = get_logger(__name__)


class OCRBackend(ABC):
    """Abstract OCR backend."""

    provider: OCRProvider

    @abstractmethod
    def extract(self, image_path: Path, language: str = "eng") -> OCRResult:
        """Extract text from an image file."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this OCR backend is usable."""


class TesseractOCR(OCRBackend):
    """Tesseract OCR backend.

    Requires: tesseract binary installed
    Install: apt install tesseract-ocr (Linux) or brew install tesseract (macOS)
    """

    provider = OCRProvider.TESSERACT

    def is_available(self) -> bool:
        return shutil.which("tesseract") is not None

    def extract(self, image_path: Path, language: str = "eng") -> OCRResult:
        if not self.is_available():
            return OCRResult(text="[Tesseract not installed]", provider="tesseract")

        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            # Full OCR with data
            data = pytesseract.image_to_data(
                img, lang=language, output_type=pytesseract.Output.DICT
            )

            regions: list[OCRRegion] = []
            full_text_parts: list[str] = []

            for i, text in enumerate(data["text"]):
                conf = float(data["conf"][i])
                if conf < 0 or not text.strip():
                    continue
                regions.append(
                    OCRRegion(
                        text=text.strip(),
                        confidence=conf / 100.0,
                        bbox=BoundingBox(
                            x=data["left"][i],
                            y=data["top"][i],
                            width=data["width"][i],
                            height=data["height"][i],
                        ),
                        language=language,
                    )
                )
                full_text_parts.append(text.strip())

            full_text = " ".join(full_text_parts)
            avg_conf = sum(r.confidence for r in regions) / len(regions) if regions else 0.0

            return OCRResult(
                text=full_text,
                regions=regions,
                language=language,
                confidence=avg_conf,
                provider="tesseract",
            )
        except ImportError:
            logger.warning("pytesseract_not_installed")
            return OCRResult(
                text="[pytesseract not installed — pip install pytesseract]",
                provider="tesseract",
            )
        except Exception as exc:
            logger.error("tesseract_ocr_failed", error=str(exc))
            return OCRResult(text=f"[OCR error: {exc}]", provider="tesseract")


class EasyOCRBackend(OCRBackend):
    """EasyOCR backend — ML-based, better accuracy on complex images."""

    provider = OCRProvider.EASYOCR
    _reader: Any = None

    def is_available(self) -> bool:
        try:
            import easyocr  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_reader(self, language: str) -> Any:
        if self._reader is not None:
            return self._reader
        try:
            import easyocr

            lang_map = {"eng": "en", "fra": "fr", "deu": "de", "spa": "es"}
            lang_code = lang_map.get(language, language[:2])
            self._reader = easyocr.Reader([lang_code], gpu=False)
            return self._reader
        except Exception:
            return None

    def extract(self, image_path: Path, language: str = "eng") -> OCRResult:
        if not self.is_available():
            return OCRResult(text="[EasyOCR not installed]", provider="easyocr")

        reader = self._get_reader(language)
        if reader is None:
            return OCRResult(text="[EasyOCR reader failed to load]", provider="easyocr")

        try:
            results = reader.readtext(str(image_path))
            regions: list[OCRRegion] = []
            text_parts: list[str] = []

            for bbox_coords, text, conf in results:
                x_min = int(min(p[0] for p in bbox_coords))
                y_min = int(min(p[1] for p in bbox_coords))
                x_max = int(max(p[0] for p in bbox_coords))
                y_max = int(max(p[1] for p in bbox_coords))

                regions.append(
                    OCRRegion(
                        text=text,
                        confidence=float(conf),
                        bbox=BoundingBox(
                            x=x_min,
                            y=y_min,
                            width=x_max - x_min,
                            height=y_max - y_min,
                        ),
                        language=language,
                    )
                )
                text_parts.append(text)

            full_text = " ".join(text_parts)
            avg_conf = sum(r.confidence for r in regions) / len(regions) if regions else 0.0
            return OCRResult(
                text=full_text,
                regions=regions,
                language=language,
                confidence=avg_conf,
                provider="easyocr",
            )
        except Exception as exc:
            logger.error("easyocr_failed", error=str(exc))
            return OCRResult(text=f"[EasyOCR error: {exc}]", provider="easyocr")


class OCREngine:
    """Unified OCR engine with automatic provider fallback.

    Tries providers in order: Tesseract → EasyOCR → minimal fallback.
    """

    def __init__(self, preferred_provider: OCRProvider = OCRProvider.TESSERACT) -> None:
        self._backends: list[OCRBackend] = []
        if preferred_provider == OCRProvider.TESSERACT:
            self._backends = [TesseractOCR(), EasyOCRBackend()]
        else:
            self._backends = [EasyOCRBackend(), TesseractOCR()]

    def extract(self, image_path: Path, language: str = "eng") -> OCRResult:
        """Extract text using the best available OCR backend."""
        for backend in self._backends:
            if backend.is_available():
                return backend.extract(image_path, language)

        # No backend available
        return OCRResult(
            text="[No OCR engine available — install tesseract or easyocr]",
            provider="none",
            confidence=0.0,
        )

    def get_available_providers(self) -> list[str]:
        """List available OCR providers."""
        return [b.provider.value for b in self._backends if b.is_available()]
