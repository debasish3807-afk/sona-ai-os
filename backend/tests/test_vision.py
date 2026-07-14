"""Tests for Vision & OCR Engine (Phase 20.3)."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import pytest

from vision.engine import VisionEngine
from vision.image_analysis import ImageAnalyzer
from vision.ocr import EasyOCRBackend, OCREngine, TesseractOCR
from vision.pdf_ocr import PDFOCREngine
from vision.schemas import (
    BoundingBox,
    ImageAnalysis,
    ImageType,
    OCRProvider,
    OCRRegion,
    OCRResult,
    VisionSettings,
)


def _create_test_image(text: str = "Hello") -> bytes:
    """Create a minimal 1x1 PNG for testing."""
    # Minimal valid PNG (1x1 white pixel)
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _create_test_pdf() -> bytes:
    """Create a minimal PDF for testing."""
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )


class TestSchemas:
    """Test vision data models."""

    def test_ocr_result_defaults(self):
        r = OCRResult(text="hello", provider="tesseract")
        assert r.text == "hello"
        assert r.confidence == 0.0
        assert r.regions == []
        assert r.page_count == 1

    def test_bounding_box(self):
        bb = BoundingBox(x=10, y=20, width=100, height=50)
        assert bb.x == 10
        assert bb.width == 100

    def test_ocr_region(self):
        r = OCRRegion(text="word", confidence=0.95)
        assert r.confidence == 0.95
        assert r.bbox is None

    def test_image_type_enum(self):
        assert ImageType.SCREENSHOT.value == "screenshot"
        assert ImageType.CODE.value == "code"
        assert ImageType.ERROR.value == "error"

    def test_ocr_provider_enum(self):
        assert OCRProvider.TESSERACT.value == "tesseract"
        assert OCRProvider.EASYOCR.value == "easyocr"

    def test_vision_settings_defaults(self):
        s = VisionSettings()
        assert s.language == "eng"
        assert s.dpi == 300
        assert "png" in s.supported_formats

    def test_image_analysis_defaults(self):
        a = ImageAnalysis()
        assert a.image_type == ImageType.UNKNOWN
        assert a.entities == []


class TestOCREngine:
    """Test OCR engine and backends."""

    def test_tesseract_availability(self):
        t = TesseractOCR()
        assert isinstance(t.is_available(), bool)

    def test_easyocr_availability(self):
        e = EasyOCRBackend()
        assert isinstance(e.is_available(), bool)

    def test_ocr_engine_providers(self):
        engine = OCREngine()
        providers = engine.get_available_providers()
        assert isinstance(providers, list)

    def test_ocr_engine_extract_fallback(self):
        """OCR on a minimal image should not crash."""
        engine = OCREngine()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(_create_test_image())
            tmp_path = Path(tmp.name)
        try:
            result = engine.extract(tmp_path)
            assert isinstance(result, OCRResult)
            assert isinstance(result.text, str)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ocr_nonexistent_file(self):
        engine = OCREngine()
        result = engine.extract(Path("/nonexistent/image.png"))
        # Should not crash
        assert isinstance(result, OCRResult)


class TestPDFOCR:
    """Test PDF OCR engine."""

    def test_pdf_nonexistent(self):
        engine = PDFOCREngine()
        result = engine.extract(Path("/nonexistent.pdf"))
        assert "not found" in result.text.lower()

    def test_pdf_minimal(self):
        engine = PDFOCREngine()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(_create_test_pdf())
            tmp_path = Path(tmp.name)
        try:
            result = engine.extract(tmp_path)
            assert isinstance(result, OCRResult)
            assert isinstance(result.text, str)
        finally:
            tmp_path.unlink(missing_ok=True)


class TestImageAnalyzer:
    """Test image analysis."""

    def test_classify_error(self):
        analyzer = ImageAnalyzer()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(_create_test_image())
            tmp_path = Path(tmp.name)
        try:
            result = analyzer.analyze(tmp_path)
            assert isinstance(result, ImageAnalysis)
            assert result.image_type in ImageType
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_analyze_nonexistent(self):
        analyzer = ImageAnalyzer()
        result = analyzer.analyze(Path("/nonexistent.png"))
        assert "not found" in result.description.lower()

    def test_entity_extraction(self):
        analyzer = ImageAnalyzer()
        entities = analyzer._extract_entities(
            "Visit https://example.com and check /usr/local/bin/python"
        )
        assert any("example.com" in e for e in entities)

    def test_classify_code_text(self):
        analyzer = ImageAnalyzer()
        img_type = analyzer._classify_type("def hello():\n    return 42", Path("code.png"))
        assert img_type == ImageType.CODE

    def test_classify_error_text(self):
        analyzer = ImageAnalyzer()
        img_type = analyzer._classify_type("Traceback (most recent call last):", Path("err.png"))
        assert img_type == ImageType.ERROR


class TestVisionEngine:
    """Test the unified vision engine."""

    def test_create_engine(self):
        engine = VisionEngine()
        assert engine.settings.language == "eng"

    def test_custom_settings(self):
        settings = VisionSettings(language="fra", dpi=200)
        engine = VisionEngine(settings=settings)
        assert engine.settings.language == "fra"
        assert engine.settings.dpi == 200

    def test_get_status(self):
        engine = VisionEngine()
        status = engine.get_status()
        assert "available_providers" in status
        assert "stats" in status

    def test_validate_file_missing(self):
        engine = VisionEngine()
        error = engine.validate_file(Path("/nonexistent.png"))
        assert error is not None
        assert "not found" in error.lower()

    def test_validate_file_exists(self):
        engine = VisionEngine()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(_create_test_image())
            tmp_path = Path(tmp.name)
        try:
            error = engine.validate_file(tmp_path)
            assert error is None
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ocr_from_bytes(self):
        engine = VisionEngine()
        result = engine.ocr_from_bytes(_create_test_image(), "test.png")
        assert isinstance(result, OCRResult)

    def test_analyze_from_bytes(self):
        engine = VisionEngine()
        result = engine.analyze_from_bytes(_create_test_image(), "test.png")
        assert isinstance(result, ImageAnalysis)

    def test_pdf_ocr(self):
        engine = VisionEngine()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(_create_test_pdf())
            tmp_path = Path(tmp.name)
        try:
            result = engine.pdf_ocr(tmp_path)
            assert isinstance(result, OCRResult)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_stats_increment(self):
        engine = VisionEngine()
        engine.ocr_from_bytes(_create_test_image())
        engine.analyze_from_bytes(_create_test_image())
        status = engine.get_status()
        assert status["stats"]["ocr_requests"] == 1
        assert status["stats"]["analyses"] == 1


class TestVisionAPI:
    """Test Vision API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.vision import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_ocr_endpoint(self, client):
        img_b64 = base64.b64encode(_create_test_image()).decode()
        resp = client.post("/vision/ocr", json={"image_base64": img_b64})
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "provider" in data
        assert "confidence" in data

    def test_ocr_invalid_base64(self, client):
        resp = client.post("/vision/ocr", json={"image_base64": "!!invalid!!"})
        assert resp.status_code == 200
        data = resp.json()
        # Either error key or fallback OCR result (base64 may decode to garbage)
        assert "error" in data or "text" in data

    def test_analyze_endpoint(self, client):
        img_b64 = base64.b64encode(_create_test_image()).decode()
        resp = client.post("/vision/analyze", json={"image_base64": img_b64})
        assert resp.status_code == 200
        data = resp.json()
        assert "image_type" in data
        assert "description" in data

    def test_pdf_endpoint(self, client):
        pdf_b64 = base64.b64encode(_create_test_pdf()).decode()
        resp = client.post("/vision/pdf", json={"pdf_base64": pdf_b64})
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "provider" in data

    def test_status_endpoint(self, client):
        resp = client.get("/vision/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "available_providers" in data
        assert "stats" in data

    def test_settings_get(self, client):
        resp = client.get("/vision/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "eng"
        assert data["dpi"] == 300

    def test_settings_update(self, client):
        resp = client.patch("/vision/settings", json={"language": "fra"})
        assert resp.status_code == 200
        assert resp.json()["updated"] is True
