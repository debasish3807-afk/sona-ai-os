package com.sona.ai.data.remote.dto

import com.google.gson.annotations.SerializedName

/**
 * DTO for login requests.
 */
data class AuthRequestDto(
    @SerializedName("email")
    val email: String,

    @SerializedName("password")
    val password: String
)

/**
 * DTO for registration requests.
 */
data class RegisterRequestDto(
    @SerializedName("name")
    val name: String,

    @SerializedName("email")
    val email: String,

    @SerializedName("password")
    val password: String
)
