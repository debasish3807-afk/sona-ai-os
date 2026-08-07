package com.sona.ai.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * DTO for memory entries from the API.
 */
data class MemoryDto(
    @SerializedName("id")
    val id: String = "",

    @SerializedName("content")
    val content: String,

    @SerializedName("type")
    val type: String,

    @SerializedName("importance")
    val importance: Float,

    @SerializedName("created_at")
    val createdAt: Long = 0L
)
