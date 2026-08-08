package com.sona.ai.sync

import com.sona.ai.data.local.PendingRequestStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Queue for managing offline requests that need to be synced.
 * Persists pending requests using Room for durability across app restarts.
 */
@Singleton
class PendingRequestQueue @Inject constructor(
    private val pendingRequestStore: PendingRequestStore
) {

    /**
     * Enqueues a request for later syncing when connectivity is restored.
     */
    suspend fun enqueue(request: PendingRequest): String {
        val id = UUID.randomUUID().toString()
        val record = PendingRequestStore.PendingRequestRecord(
            id = id,
            type = request.type.name,
            endpoint = request.endpoint,
            payload = request.payload,
            timestamp = System.currentTimeMillis(),
            retryCount = 0,
            priority = request.priority
        )
        pendingRequestStore.insert(record)
        return id
    }

    /**
     * Gets all pending requests ordered by priority and timestamp.
     */
    suspend fun getPendingRequests(): List<PendingRequestEntry> {
        return pendingRequestStore.getAllPending().map { record ->
            PendingRequestEntry(
                id = record.id,
                type = record.type,
                endpoint = record.endpoint,
                payload = record.payload,
                timestamp = record.timestamp,
                retryCount = record.retryCount,
                priority = record.priority
            )
        }
    }

    /**
     * Observes the count of pending requests.
     */
    fun observePendingCount(): Flow<Int> {
        return pendingRequestStore.observeCount()
    }

    /**
     * Marks a request as completed and removes it from the queue.
     */
    suspend fun markCompleted(id: String) {
        pendingRequestStore.delete(id)
    }

    /**
     * Increments the retry count for a failed request.
     */
    suspend fun markRetry(id: String) {
        pendingRequestStore.incrementRetry(id)
    }

    /**
     * Removes requests that have exceeded max retry count.
     */
    suspend fun purgeExpiredRequests(maxRetries: Int = 5) {
        pendingRequestStore.deleteExceededRetries(maxRetries)
    }

    /**
     * Clears all pending requests.
     */
    suspend fun clear() {
        pendingRequestStore.clearAll()
    }
}

/**
 * A request pending synchronization.
 */
data class PendingRequest(
    val type: RequestType,
    val endpoint: String,
    val payload: String,
    val priority: Int = 0
)

/**
 * Types of pending requests.
 */
enum class RequestType {
    CHAT_MESSAGE,
    FILE_UPLOAD,
    MEMORY_CREATE,
    MEMORY_DELETE,
    AGENT_EXECUTE
}

/**
 * Stored entry for a pending request.
 */
data class PendingRequestEntry(
    val id: String,
    val type: String,
    val endpoint: String,
    val payload: String,
    val timestamp: Long,
    val retryCount: Int,
    val priority: Int
)
