"""Image analysis — classify and understand image content.

Provides heuristic-based image type detection and content extraction.
For AI-powered analysis, integrates with the AI pipeline (Ollama vision).
"""

from __future__ import annotations

import re
from pathlib import Path

from config.logging import get_logger
from vision.ocr import OCREngine
from vision.schemas import ImageAnalysis, ImageType

logger = get_logger(__name__)


class ImageAnalyzer:
    """Analyzes images to determine content type and extract information."""

    def __init__(self, ocr_engine: OCREngine | None = None) -> None:
        self._ocr = ocr_engine or OCREngine()

    def analyze(self, image_path: Path, language: str = "eng") -> ImageAnalysis:
        """Analyze an image: classify type, extract text, identify entities.

        Uses OCR + heuristics to understand the image content.
        """
        if not image_path.exists():
            return ImageAnalysis(description="File not found")

        # Run OCR
        ocr_result = self._ocr.extract(image_path, language)
        text = ocr_result.text

        # Classify image type
        image_type = self._classify_type(text, image_path)

        # Extract entities
        entities = self._extract_entities(text)

        # Generate description
        description = self._generate_description(image_type, text, entities)

        return ImageAnalysis(
            image_type=image_type,
            description=description,
            extracted_text=text,
            entities=entities,
            confidence=ocr_result.confidence,
            metadata={
                "ocr_provider": ocr_result.provider,
                "region_count": len(ocr_result.regions),
                "file_name": image_path.name,
            },
        )

    def _classify_type(self, text: str, path: Path) -> ImageType:
        """Classify image content type based on OCR text and filename."""
        text_lower = text.lower()
        name_lower = path.name.lower()

        # Error screenshots
        if any(
            kw in text_lower
            for kw in [
                "error",
                "exception",
                "traceback",
                "fatal",
                "crash",
                "segfault",
                "panic",
                "failed",
                "permission denied",
            ]
        ):
            return ImageType.ERROR

        # Code screenshots
        if any(
            kw in text_lower
            for kw in [
                "def ",
                "class ",
                "import ",
                "function",
                "const ",
                "return ",
                "if (",
                "for (",
                "while ",
                "=>",
                "->",
            ]
        ):
            return ImageType.CODE

        # Screenshots (UI elements)
        if any(
            kw in text_lower
            for kw in [
                "file",
                "edit",
                "view",
                "window",
                "help",
                "settings",
                "preferences",
                "menu",
                "toolbar",
            ]
        ) and any(kw in name_lower for kw in ["screenshot", "screen", "capture"]):
            return ImageType.SCREENSHOT

        # Diagrams
        if (
            any(
                kw in text_lower
                for kw in [
                    "start",
                    "end",
                    "yes",
                    "no",
                    "decision",
                ]
            )
            or "diagram" in name_lower
            or "flowchart" in name_lower
        ):
            return ImageType.DIAGRAM

        # Documents
        if len(text) > 200:
            return ImageType.DOCUMENT

        if "screenshot" in name_lower or "screen" in name_lower:
            return ImageType.SCREENSHOT

        return ImageType.UNKNOWN

    def _extract_entities(self, text: str) -> list[str]:
        """Extract notable entities from OCR text."""
        entities: list[str] = []

        # URLs
        urls = re.findall(r"https?://[^\s]+", text)
        entities.extend(urls[:5])

        # File paths
        paths = re.findall(r"[/\\][\w./\\-]+\.\w+", text)
        entities.extend(paths[:5])

        # Error codes
        errors = re.findall(r"[A-Z]\d{3,5}|Error \d+|errno \d+", text)
        entities.extend(errors[:5])

        # Function/class names
        code = re.findall(r"\b(?:def|class|function)\s+(\w+)", text)
        entities.extend(code[:5])

        return entities

    def _generate_description(self, image_type: ImageType, text: str, entities: list[str]) -> str:
        """Generate a human-readable description of the image."""
        type_desc = {
            ImageType.SCREENSHOT: "Screenshot of application UI",
            ImageType.DOCUMENT: "Document or text content",
            ImageType.DIAGRAM: "Diagram or flowchart",
            ImageType.CODE: "Code or terminal output",
            ImageType.ERROR: "Error message or crash report",
            ImageType.PHOTO: "Photograph",
            ImageType.UNKNOWN: "Image content",
        }

        desc = type_desc.get(image_type, "Image")
        if text and len(text) > 10:
            preview = text[:100].replace("\n", " ").strip()
            desc += f' — "{preview}..."'
        if entities:
            desc += f" (contains: {', '.join(entities[:3])})"
        return desc
