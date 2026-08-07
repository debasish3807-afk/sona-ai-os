package com.sona.ai.features.connectors.runtime

import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Rate limiter that enforces a minimum interval between requests
 * on a per-connector basis. Prevents API abuse and respects
 * external service rate limits.
 */
@Singleton
class RateLimiter @Inject constructor() {

    private val lastRequest = mutableMapOf<String, Long>()
    private val minInterval = 1000L // 1 request per second per connector

    /**
     * Acquire permission to make a request for the given connector.
     * Will suspend (delay) if the minimum interval has not elapsed.
     */
    suspend fun acquire(connectorId: String) {
        val last = lastRequest[connectorId] ?: 0
        val elapsed = System.currentTimeMillis() - last
        if (elapsed < minInterval) {
            delay(minInterval - elapsed)
        }
        lastRequest[connectorId] = System.currentTimeMillis()
    }
}
