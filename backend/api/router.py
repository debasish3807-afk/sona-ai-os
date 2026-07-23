"""API router factory — assembles all route modules."""

from fastapi import APIRouter

from api.adapters import router as adapters_router
from api.agents import router as agents_router
from api.auth import router as auth_router
from api.automation import router as automation_router
from api.automation_v2 import router as automation_v2_router
from api.capabilities import router as capabilities_router
from api.chat import router as chat_router
from api.coding import router as coding_router
from api.cognitive import router as cognitive_router
from api.documents import router as documents_router
from api.execute import router as execute_router
from api.executive import router as executive_router
from api.health import router as health_router
from api.memory import router as memory_router
from api.meta_reasoning import router as meta_reasoning_router
from api.microkernel import router as microkernel_router
from api.orchestration import router as orchestration_router
from api.plugins import router as plugins_router
from api.research import router as research_router
from api.runtime_workflows import router as runtime_workflows_router
from api.tools import router as tools_router
from api.v1.router import router as v1_router
from api.version import router as version_router
from api.vision import router as vision_router
from api.voice import router as voice_router
from api.workspace import router as workspace_router
from knowledge.router import router as knowledge_router


def create_api_router() -> APIRouter:
    """Create and configure the main API router.

    Assembles all sub-routers into a unified API router
    with proper prefixing and tagging.

    Returns:
        Configured APIRouter instance.
    """
    api_router = APIRouter()

    # ─── Versioned API (v1) — production-grade with Pydantic models ──────
    api_router.include_router(v1_router)

    # ─── Legacy routes (backward compatible) ─────────────────────────────

    # Health and system routes (public)
    api_router.include_router(orchestration_router)
    api_router.include_router(health_router)
    api_router.include_router(version_router)

    # Authentication routes (public)
    api_router.include_router(auth_router)

    # AI Coding Assistant routes
    api_router.include_router(coding_router)

    # AI Brain chat routes
    api_router.include_router(chat_router)

    # MCP Tool system routes
    api_router.include_router(tools_router)

    # Execution & function calling routes
    api_router.include_router(execute_router)

    # Knowledge engine (documents & memory search)
    api_router.include_router(documents_router)

    # Cognitive Kernel endpoints
    api_router.include_router(cognitive_router)

    # Dynamic Capability Fabric endpoints
    api_router.include_router(capabilities_router)

    # Executive Intelligence endpoints
    api_router.include_router(executive_router)

    # Meta Reasoning & Self Reflection endpoints
    api_router.include_router(meta_reasoning_router)

    # Microkernel runtime endpoints
    api_router.include_router(microkernel_router)

    # Runtime integration (adapters) endpoints
    api_router.include_router(adapters_router)

    # Runtime workflow engine endpoints
    api_router.include_router(runtime_workflows_router)

    # Deep Research Engine endpoints
    api_router.include_router(research_router)

    # Desktop Workspace API
    api_router.include_router(workspace_router)

    # Voice AI Assistant
    api_router.include_router(voice_router)

    # Vision & OCR Engine
    api_router.include_router(agents_router)
    api_router.include_router(knowledge_router)
    api_router.include_router(memory_router)
    api_router.include_router(vision_router)

    # Automation Engine
    api_router.include_router(automation_router)
    api_router.include_router(automation_v2_router)

    # Plugin & MCP Ecosystem
    api_router.include_router(plugins_router)

    return api_router
