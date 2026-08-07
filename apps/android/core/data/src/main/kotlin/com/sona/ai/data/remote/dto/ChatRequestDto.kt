package com.sona.ai.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * DTO for sending chat completion requests.
 */
data class ChatRequestDto(
    @SerializedName("conversation_id")
    val conversationId: String,

    @SerializedName("message")
    val message: String,

    @SerializedName("model")
    val model: String = "sona-v1",

    @SerializedName("temperature")
    val temperature: Float = 0.7f,

    @SerializedName("max_tokens")
    val maxTokens: Int = 4096,

    @SerializedName("stream")
    val stream: Boolean = false
)
