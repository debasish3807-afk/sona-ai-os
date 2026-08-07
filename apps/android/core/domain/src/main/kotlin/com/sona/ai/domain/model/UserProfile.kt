package com.sona.ai.domain.model

/**
 * Represents the authenticated user's profile.
 */
data class UserProfile(
    val id: String,
    val name: String,
    val email: String,
    val token: String,
    val avatarUrl: String = ""
)
