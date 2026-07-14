package com.sona.ai.data.api

import com.sona.ai.domain.model.*
import retrofit2.http.*

/**
 * Retrofit interface for the Sona AI OS backend API.
 *
 * Connects to workspace, voice, vision, research, and memory endpoints.
 */
interface SonaApi {

    // ─── Chat ────────────────────────────────────────────────────────────

    @POST("workspace/chat/complete")
    suspend fun chatComplete(@Body request: ChatRequest): ChatResponse

    // ─── Voice ───────────────────────────────────────────────────────────

    @POST("voice/transcribe")
    suspend fun transcribe(@Body request: TranscribeRequest): TranscribeResponse

    @POST("voice/synthesize")
    suspend fun synthesize(@Body request: SynthesizeRequest): okhttp3.ResponseBody

    @POST("voice/process")
    suspend fun processVoice(@Body request: ProcessVoiceRequest): ProcessVoiceResponse

    @GET("voice/status")
    suspend fun voiceStatus(): VoiceStatusResponse

    // ─── Vision ──────────────────────────────────────────────────────────

    @POST("vision/ocr")
    suspend fun ocrImage(@Body request: OCRRequest): OCRResponse

    @POST("vision/analyze")
    suspend fun analyzeImage(@Body request: AnalyzeRequest): AnalyzeResponse

    @POST("vision/pdf")
    suspend fun ocrPdf(@Body request: PDFRequest): PDFResponse

    @GET("vision/status")
    suspend fun visionStatus(): VisionStatusResponse

    // ─── Research ────────────────────────────────────────────────────────

    @POST("research/deep")
    suspend fun deepResearch(@Body request: ResearchRequest): ResearchResponse

    // ─── Memory ──────────────────────────────────────────────────────────

    @GET("workspace/memory")
    suspend fun listMemories(
        @Query("query") query: String = "",
        @Query("memory_type") memoryType: String = "",
        @Query("limit") limit: Int = 50
    ): MemoryListResponse

    @POST("workspace/memory")
    suspend fun storeMemory(@Body entry: MemoryStoreRequest): MemoryStoreResponse

    @DELETE("workspace/memory/{id}")
    suspend fun deleteMemory(@Path("id") memoryId: String): DeleteResponse

    // ─── Files ───────────────────────────────────────────────────────────

    @GET("workspace/files")
    suspend fun listFiles(
        @Query("path") path: String = "",
        @Query("depth") depth: Int = 1
    ): FileListResponse

    @GET("workspace/files/content")
    suspend fun readFile(@Query("path") path: String): FileContentResponse

    // ─── Terminal ────────────────────────────────────────────────────────

    @POST("workspace/terminal")
    suspend fun executeCommand(@Body request: TerminalRequest): okhttp3.ResponseBody

    // ─── Settings ────────────────────────────────────────────────────────

    @GET("workspace/settings")
    suspend fun getSettings(): SettingsResponse

    @PATCH("workspace/settings")
    suspend fun updateSettings(@Body settings: SettingsUpdateRequest): SettingsUpdateResponse
}
