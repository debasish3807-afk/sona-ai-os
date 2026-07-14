package com.sona.ai.domain.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─── Chat ────────────────────────────────────────────────────────────────────

@Serializable
data class ChatMessage(
    val role: String = "user",
    val content: String
)

@Serializable
data class ChatRequest(
    val messages: List<ChatMessage>,
    val model: String = "",
    val provider: String = "",
    val temperature: Double = 0.7,
    @SerialName("max_tokens") val maxTokens: Int = 4096,
    val stream: Boolean = false,
    @SerialName("system_prompt") val systemPrompt: String = ""
)

@Serializable
data class ChatResponse(
    val content: String,
    val model: String = "",
    val provider: String = "",
    @SerialName("tokens_used") val tokensUsed: Int = 0,
    @SerialName("latency_ms") val latencyMs: Double = 0.0
)

// ─── Voice ───────────────────────────────────────────────────────────────────

@Serializable
data class TranscribeRequest(
    @SerialName("audio_base64") val audioBase64: String,
    val language: String = "en"
)

@Serializable
data class TranscribeResponse(
    val text: String,
    val language: String = "",
    val confidence: Double = 0.0,
    @SerialName("is_final") val isFinal: Boolean = true
)

@Serializable
data class SynthesizeRequest(val text: String, val voice: String = "")

@Serializable
data class ProcessVoiceRequest(@SerialName("audio_base64") val audioBase64: String)

@Serializable
data class ProcessVoiceResponse(
    val transcription: String = "",
    val action: String = "",
    val command: String = "",
    val message: String = "",
    val confidence: Double = 0.0
)

@Serializable
data class VoiceStatusResponse(
    val transcriptions: Int = 0,
    val syntheses: Int = 0,
    @SerialName("stt_available") val sttAvailable: Boolean = false,
    val language: String = "en"
)

// ─── Vision ──────────────────────────────────────────────────────────────────

@Serializable
data class OCRRequest(
    @SerialName("image_base64") val imageBase64: String,
    val filename: String = "image.png",
    val language: String = ""
)

@Serializable
data class OCRResponse(
    val text: String = "",
    val confidence: Double = 0.0,
    val provider: String = "",
    @SerialName("region_count") val regionCount: Int = 0,
    val language: String = ""
)

@Serializable
data class AnalyzeRequest(
    @SerialName("image_base64") val imageBase64: String,
    val filename: String = "image.png"
)

@Serializable
data class AnalyzeResponse(
    @SerialName("image_type") val imageType: String = "unknown",
    val description: String = "",
    @SerialName("extracted_text") val extractedText: String = "",
    val entities: List<String> = emptyList(),
    val confidence: Double = 0.0
)

@Serializable
data class PDFRequest(
    @SerialName("pdf_base64") val pdfBase64: String,
    val language: String = ""
)

@Serializable
data class PDFResponse(
    val text: String = "",
    @SerialName("page_count") val pageCount: Int = 0,
    val pages: List<String> = emptyList(),
    val confidence: Double = 0.0
)

@Serializable
data class VisionStatusResponse(
    @SerialName("available_providers") val availableProviders: List<String> = emptyList()
)

// ─── Research ────────────────────────────────────────────────────────────────

@Serializable
data class ResearchRequest(
    val query: String,
    val offline: Boolean = false,
    @SerialName("use_cache") val useCache: Boolean = true
)

@Serializable
data class ResearchResponse(
    val ok: Boolean = false,
    val report: ResearchReport? = null
)

@Serializable
data class ResearchReport(
    val query: String = "",
    @SerialName("executive_summary") val executiveSummary: String = "",
    @SerialName("confidence_score") val confidenceScore: Double = 0.0,
    val recommendations: List<String> = emptyList()
)

// ─── Memory ──────────────────────────────────────────────────────────────────

@Serializable
data class MemoryListResponse(
    val memories: List<MemoryItem> = emptyList(),
    val count: Int = 0
)

@Serializable
data class MemoryItem(
    val id: String = "",
    val content: String = "",
    val type: String = ""
)

@Serializable
data class MemoryStoreRequest(
    val content: String,
    @SerialName("memory_type") val memoryType: String = "conversation",
    val importance: Double = 0.5,
    val tags: List<String> = emptyList()
)

@Serializable
data class MemoryStoreResponse(
    @SerialName("memory_id") val memoryId: String = "",
    val stored: Boolean = false
)

@Serializable
data class DeleteResponse(val deleted: Boolean = false)

// ─── Files ───────────────────────────────────────────────────────────────────

@Serializable
data class FileListResponse(
    val path: String = "",
    val nodes: List<FileNode> = emptyList()
)

@Serializable
data class FileNode(
    val name: String,
    val path: String,
    @SerialName("is_dir") val isDir: Boolean,
    val size: Long = 0,
    val extension: String = ""
)

@Serializable
data class FileContentResponse(
    val type: String = "",
    val content: String = "",
    val path: String = "",
    val error: String = ""
)

// ─── Terminal ────────────────────────────────────────────────────────────────

@Serializable
data class TerminalRequest(
    val command: String,
    val cwd: String = "",
    val timeout: Int = 30
)

// ─── Settings ────────────────────────────────────────────────────────────────

@Serializable
data class SettingsResponse(
    val provider: String = "ollama",
    val model: String = "llama3",
    val theme: String = "dark",
    val temperature: Double = 0.7,
    @SerialName("max_tokens") val maxTokens: Int = 4096,
    @SerialName("research_depth") val researchDepth: String = "standard"
)

@Serializable
data class SettingsUpdateRequest(
    val provider: String = "",
    val model: String = "",
    val theme: String = "",
    val temperature: Double? = null,
    @SerialName("max_tokens") val maxTokens: Int? = null
)

@Serializable
data class SettingsUpdateResponse(
    val updated: Boolean = false,
    val settings: SettingsResponse? = null
)
