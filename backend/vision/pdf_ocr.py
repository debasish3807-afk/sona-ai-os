"""PDF OCR — extract text from scanned PDF documents.

Supports multi-page PDFs with page-level OCR results.
Falls back gracefully when pdf2image or poppler not available.
"""

from __future__ import annotations

from pathlib import Path

from config.logging import get_logger
from vision.ocr import OCREngine
from vision.schemas import OCRResult

logger = get_logger(__name__)


class PDFOCREngine:
    """Extracts text from scanned PDFs via page-by-page OCR."""

    def __init__(self, ocr_engine: OCREngine | None = None, dpi: int = 300) -> None:
        self._ocr = ocr_engine or OCREngine()
        self._dpi = dpi

    def extract(self, pdf_path: Path, language: str = "eng") -> OCRResult:
        """Extract text from all pages of a PDF.

        Converts each page to an image, runs OCR, and merges results.
        Falls back to text extraction if pdf2image unavailable.
        """
        if not pdf_path.exists():
            return OCRResult(text="[File not found]", provider="pdf_ocr")

        # Try pdf2image first (requires poppler)
        pages_text = self._extract_with_pdf2image(pdf_path, language)
        if pages_text is not None:
            full_text = "\n\n".join(f"--- Page {i + 1} ---\n{t}" for i, t in enumerate(pages_text))
            return OCRResult(
                text=full_text,
                language=language,
                provider="pdf_ocr",
                page_count=len(pages_text),
                pages=pages_text,
                confidence=0.8,
            )

        # Try PyPDF2/pypdf for text-based PDFs
        text = self._extract_with_pypdf(pdf_path)
        if text:
            return OCRResult(
                text=text,
                language=language,
                provider="pypdf",
                page_count=1,
                pages=[text],
                confidence=0.9,
            )

        return OCRResult(
            text="[PDF extraction unavailable — install pdf2image and poppler, or pypdf]",
            provider="pdf_ocr",
            confidence=0.0,
        )

    def _extract_with_pdf2image(self, pdf_path: Path, language: str) -> list[str] | None:
        """Convert PDF pages to images and OCR each page."""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_path), dpi=self._dpi)
            pages: list[str] = []

            for _i, img in enumerate(images):
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                    img.save(tmp_path, "PNG")

                try:
                    result = self._ocr.extract(tmp_path, language)
                    pages.append(result.text)
                finally:
                    tmp_path.unlink(missing_ok=True)

            return pages if pages else None
        except ImportError:
            logger.debug("pdf2image_not_available")
            return None
        except Exception as exc:
            logger.error("pdf2image_failed", error=str(exc))
            return None

    def _extract_with_pypdf(self, pdf_path: Path) -> str | None:
        """Extract text from text-based PDFs using pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text.strip())
            return "\n\n".join(pages) if pages else None
        except ImportError:
            return None
        except Exception:
            return None
