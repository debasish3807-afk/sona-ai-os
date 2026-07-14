package com.sona.ai.data.repository

import com.sona.ai.data.api.SonaApi
import com.sona.ai.data.local.ConversationDatabase
import com.sona.ai.data.local.ConversationEntity
import com.sona.ai.data.local.MessageEntity
import com.sona.ai.domain.model.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Single source of truth for all Sona data.
 *
 * Handles network calls with offline fallback via Room database.
 */
@Singleton
class SonaRepository @Inject constructor(
    private val api: SonaApi,
    private val db: ConversationDatabase
) {
    // ─── Chat ────────────────────────────────────────────────────────────

    suspend fun sendMessage(messages: List<ChatMessage>, model: String = ""): Result<ChatResponse> {
        return runCatching {
            api.chatComplete(ChatRequest(messages = messages, model = model))
        }
    }

    // ─── Voice ───────────────────────────────────────────────────────────

    suspend fun transcribe(audioBase64: String): Result<TranscribeResponse> {
        return runCatching { api.transcribe(TranscribeRequest(audioBase64)) }
    }

    suspend fun processVoice(audioBase64: String): Result<ProcessVoiceResponse> {
        return runCatching { api.processVoice(ProcessVoiceRequest(audioBase64)) }
    }

    // ─── Vision ──────────────────────────────────────────────────────────

    suspend fun ocrImage(imageBase64: String, filename: String = "image.png"): Result<OCRResponse> {
        return runCatching { api.ocrImage(OCRRequest(imageBase64, filename)) }
    }

    suspend fun analyzeImage(imageBase64: String): Result<AnalyzeResponse> {
        return runCatching { api.analyzeImage(AnalyzeRequest(imageBase64)) }
    }

    suspend fun ocrPdf(pdfBase64: String): Result<PDFResponse> {
        return runCatching { api.ocrPdf(PDFRequest(pdfBase64)) }
    }

    // ─── Research ────────────────────────────────────────────────────────

    suspend fun deepResearch(query: String, offline: Boolean = false): Result<ResearchResponse> {
        return runCatching { api.deepResearch(ResearchRequest(query, offline)) }
    }

    // ─── Memory ──────────────────────────────────────────────────────────

    suspend fun searchMemory(query: String): Result<MemoryListResponse> {
        return runCatching { api.listMemories(query = query) }
    }

    suspend fun storeMemory(content: String, type: String = "conversation"): Result<MemoryStoreResponse> {
        return runCatching { api.storeMemory(MemoryStoreRequest(content, type)) }
    }

    suspend fun deleteMemory(id: String): Result<DeleteResponse> {
        return runCatching { api.deleteMemory(id) }
    }

    // ─── Files ───────────────────────────────────────────────────────────

    suspend fun listFiles(path: String = ""): Result<FileListResponse> {
        return runCatching { api.listFiles(path) }
    }

    suspend fun readFile(path: String): Result<FileContentResponse> {
        return runCatching { api.readFile(path) }
    }

    // ─── Settings ────────────────────────────────────────────────────────

    suspend fun getSettings(): Result<SettingsResponse> {
        return runCatching { api.getSettings() }
    }

    suspend fun updateSettings(provider: String = "", model: String = ""): Result<SettingsUpdateResponse> {
        return runCatching { api.updateSettings(SettingsUpdateRequest(provider, model)) }
    }

    // ─── Local Storage (Offline) ─────────────────────────────────────────

    suspend fun saveMessageLocally(convId: String, role: String, content: String) {
        db.messageDao().insert(MessageEntity(conversationId = convId, role = role, content = content))
    }

    suspend fun getLocalMessages(convId: String): List<MessageEntity> {
        return db.messageDao().getMessages(convId)
    }

    suspend fun getLocalConversations(): List<ConversationEntity> {
        return db.conversationDao().getAll()
    }

    suspend fun createLocalConversation(id: String, title: String) {
        db.conversationDao().insert(ConversationEntity(id = id, title = title))
    }

    suspend fun deleteLocalConversation(id: String) {
        db.conversationDao().delete(id)
        db.messageDao().deleteByConversation(id)
    }
}
