package com.sona.ai.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * DTO for authentication responses (login/register).
 */
data class AuthResponseDto(
    @SerializedName("user_id")
    val userId: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("email")
    val email: String,

    @SerializedName("token")
    val token: String,

    @SerializedName("avatar_url")
    val avatarUrl: String = ""
)
