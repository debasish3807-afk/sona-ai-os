package com.sona.ai.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * DTO for chat completion responses from the API.
 */
data class ChatResponseDto(
    @SerializedName("id")
    val id: String,

    @SerializedName("conversation_id")
    val conversationId: String,

    @SerializedName("content")
    val content: String,

    @SerializedName("role")
    val role: String,

    @SerializedName("model")
    val model: String,

    @SerializedName("created_at")
    val createdAt: Long,

    @SerializedName("usage")
    val usage: UsageDto? = null
)

/**
 * Token usage information.
 */
data class UsageDto(
    @SerializedName("prompt_tokens")
    val promptTokens: Int,

    @SerializedName("completion_tokens")
    val completionTokens: Int,

    @SerializedName("total_tokens")
    val totalTokens: Int
)
