package com.sona.ai.data.remote

import com.sona.ai.data.remote.dto.AuthRequestDto
import com.sona.ai.data.remote.dto.AuthResponseDto
import com.sona.ai.data.remote.dto.ChatRequestDto
import com.sona.ai.data.remote.dto.ChatResponseDto
import com.sona.ai.data.remote.dto.MemoryDto
import com.sona.ai.data.remote.dto.RegisterRequestDto
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Streaming

/**
 * Retrofit API interface for the Sona AI backend.
 */
interface SonaApi {

    // ─── Chat ───────────────────────────────────────────────────────────

    @POST("api/v1/chat/completions")
    suspend fun sendMessage(
        @Body request: ChatRequestDto
    ): ChatResponseDto

    @Streaming
    @POST("api/v1/chat/completions/stream")
    suspend fun streamMessage(
        @Body request: ChatRequestDto
    ): Response<ResponseBody>

    // ─── Auth ───────────────────────────────────────────────────────────

    @POST("api/v1/auth/login")
    suspend fun login(
        @Body request: AuthRequestDto
    ): AuthResponseDto

    @POST("api/v1/auth/register")
    suspend fun register(
        @Body request: RegisterRequestDto
    ): AuthResponseDto

    @POST("api/v1/auth/logout")
    suspend fun logout(
        @Header("Authorization") token: String
    )

    // ─── Memory ─────────────────────────────────────────────────────────

    @GET("api/v1/memories")
    suspend fun getMemories(): List<MemoryDto>

    @GET("api/v1/memories/search")
    suspend fun searchMemories(
        @Query("q") query: String
    ): List<MemoryDto>

    @POST("api/v1/memories")
    suspend fun createMemory(
        @Body memory: MemoryDto
    ): MemoryDto

    @DELETE("api/v1/memories/{id}")
    suspend fun deleteMemory(
        @Path("id") memoryId: String
    )

    // ─── Health ─────────────────────────────────────────────────────────

    @GET("api/v1/health")
    suspend fun healthCheck(): Response<Unit>

    // ─── Files ──────────────────────────────────────────────────────────

    @POST("api/v1/files/upload")
    suspend fun uploadFile(
        @Query("fileName") fileName: String,
        @Query("mimeType") mimeType: String,
        @Body content: ByteArray
    ): FileAnalysisResponse

    @POST("api/v1/files/text")
    suspend fun uploadTextContent(
        @Query("fileName") fileName: String,
        @Body content: String
    ): FileAnalysisResponse

    @POST("api/v1/vision/analyze")
    suspend fun analyzeImage(
        @Query("imagePath") imagePath: String
    ): FileAnalysisResponse

    // ─── Agents ─────────────────────────────────────────────────────────

    @GET("api/v1/agents")
    suspend fun getAgents(): List<AgentDto>

    @POST("api/v1/agents/{agentId}/execute")
    suspend fun executeAgent(
        @Path("agentId") agentId: String,
        @Body request: AgentExecuteRequest
    ): AgentExecuteResponse

    @GET("api/v1/agents/executions/{executionId}")
    suspend fun getAgentExecutionStatus(
        @Path("executionId") executionId: String
    ): AgentExecutionStatusDto

    @POST("api/v1/agents/executions/{executionId}/cancel")
    suspend fun cancelAgentExecution(
        @Path("executionId") executionId: String
    )

}
/**
 * Response from file/image analysis.
 */
data class FileAnalysisResponse(
    val analysis: String,
    val fileName: String? = null
)
