package com.sona.ai.features.connectors.runtime

import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Sync engine that handles incremental data synchronization
 * with external services. Implements exponential backoff retry
 * and rate limiting to handle transient failures gracefully.
 */
@Singleton
class SyncEngine @Inject constructor(
    private val rateLimiter: RateLimiter
) {

    /**
     * Perform a sync operation for the given connector with retry logic.
     * Uses exponential backoff: 2s, 4s, 8s between retries.
     *
     * @param connector The connector to sync
     * @param maxRetries Maximum number of retry attempts (default 3)
     * @return SyncResult indicating success/failure and items synced
     */
    suspend fun sync(connector: Connector, maxRetries: Int = 3): SyncResult {
        var attempt = 0
        while (attempt < maxRetries) {
            try {
                rateLimiter.acquire(connector.id)
                return connector.sync()
            } catch (e: Exception) {
                attempt++
                if (attempt >= maxRetries) {
                    return SyncResult(
                        success = false,
                        errors = listOf(e.message ?: "Sync failed after $maxRetries attempts")
                    )
                }
                // Exponential backoff: 2^attempt seconds
                delay(1000L * (1 shl attempt))
            }
        }
        return SyncResult(success = false, errors = listOf("Max retries exceeded"))
    }
}
