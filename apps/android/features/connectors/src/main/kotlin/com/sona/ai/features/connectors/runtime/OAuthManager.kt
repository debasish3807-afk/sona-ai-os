package com.sona.ai.features.connectors.runtime

import java.security.MessageDigest
import java.util.Base64
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * OAuth 2.0 configuration for a connector service.
 */
data class OAuthConfig(
    val clientId: String,
    val authUrl: String,
    val tokenUrl: String,
    val redirectUri: String,
    val scopes: List<String>
)

/**
 * Manages OAuth 2.0 + PKCE (Proof Key for Code Exchange) flows.
 * Generates code verifiers, challenges, builds auth URLs,
 * and handles token exchange.
 */
@Singleton
class OAuthManager @Inject constructor(
    private val tokenManager: TokenManager
) {

    /**
     * Generate a cryptographically random code verifier for PKCE.
     * Returns a 64-character string of hex characters.
     */
    fun generateCodeVerifier(): String {
        return UUID.randomUUID().toString().replace("-", "") +
            UUID.randomUUID().toString().replace("-", "")
    }

    /**
     * Generate a SHA-256 code challenge from the verifier for PKCE.
     * Uses S256 challenge method as recommended by RFC 7636.
     */
    fun generateCodeChallenge(verifier: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(verifier.toByteArray())
        return Base64.getUrlEncoder().withoutPadding().encodeToString(digest)
    }

    /**
     * Build the full authorization URL with PKCE parameters.
     */
    fun buildAuthUrl(
        config: OAuthConfig,
        codeChallenge: String,
        state: String
    ): String {
        return "${config.authUrl}?" +
            "client_id=${config.clientId}&" +
            "redirect_uri=${config.redirectUri}&" +
            "scope=${config.scopes.joinToString("+")}&" +
            "response_type=code&" +
            "code_challenge=$codeChallenge&" +
            "code_challenge_method=S256&" +
            "state=$state"
    }

    /**
     * Exchange an authorization code for tokens.
     * In production, this would make an HTTP POST to the token endpoint.
     */
    suspend fun exchangeCode(
        connectorId: String,
        code: String,
        config: OAuthConfig,
        codeVerifier: String
    ): OAuthToken {
        val token = OAuthToken(
            accessToken = "token_$code",
            refreshToken = "refresh_$code",
            expiresAt = System.currentTimeMillis() + 3600_000,
            scope = config.scopes.joinToString(" ")
        )
        tokenManager.storeToken(connectorId, token)
        return token
    }
}
