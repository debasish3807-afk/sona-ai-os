package com.sona.ai.features.connectors.runtime

import javax.inject.Inject
import javax.inject.Singleton

/**
 * OAuth token data class holding access/refresh tokens and metadata.
 */
data class OAuthToken(
    val accessToken: String,
    val refreshToken: String = "",
    val expiresAt: Long = 0,
    val scope: String = ""
)

/**
 * Manages secure storage of OAuth tokens for each connector.
 * Currently uses in-memory storage; production would use
 * EncryptedSharedPreferences via AndroidX Security.
 */
@Singleton
class TokenManager @Inject constructor() {

    private val tokens = mutableMapOf<String, OAuthToken>()

    /** Store a token for a specific connector */
    fun storeToken(connectorId: String, token: OAuthToken) {
        tokens[connectorId] = token
    }

    /** Retrieve stored token for a connector */
    fun getToken(connectorId: String): OAuthToken? = tokens[connectorId]

    /** Remove stored token (on disconnect) */
    fun clearToken(connectorId: String) {
        tokens.remove(connectorId)
    }

    /** Check if the token is expired based on expiresAt timestamp */
    fun isTokenExpired(connectorId: String): Boolean {
        return tokens[connectorId]?.let {
            it.expiresAt > 0 && it.expiresAt < System.currentTimeMillis()
        } ?: true
    }

    /** Refresh token by generating new expiry (production would call token endpoint) */
    suspend fun refreshToken(connectorId: String): OAuthToken? {
        val current = tokens[connectorId] ?: return null
        val refreshed = current.copy(
            expiresAt = System.currentTimeMillis() + 3600_000
        )
        tokens[connectorId] = refreshed
        return refreshed
    }
}
