package com.sona.ai.data.local

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Persistent store for pending requests that need to be synced.
 * Uses a local file-based approach for simplicity; could be upgraded to Room.
 */
@Singleton
class PendingRequestStore @Inject constructor(
    @ApplicationContext private val context: Context
) {

    // In-memory cache backed by file storage
    private val pendingRequests = MutableStateFlow<MutableList<PendingRequestRecord>>(mutableListOf())

    data class PendingRequestRecord(
        val id: String,
        val type: String,
        val endpoint: String,
        val payload: String,
        val timestamp: Long,
        val retryCount: Int,
        val priority: Int
    )

    /**
     * Inserts a new pending request.
     */
    suspend fun insert(entry: com.sona.ai.sync.PendingRequestEntry) {
        val record = PendingRequestRecord(
            id = entry.id,
            type = entry.type,
            endpoint = entry.endpoint,
            payload = entry.payload,
            timestamp = entry.timestamp,
            retryCount = entry.retryCount,
            priority = entry.priority
        )
        pendingRequests.value = pendingRequests.value.toMutableList().apply { add(record) }
    }

    /**
     * Gets all pending requests sorted by priority (desc) then timestamp (asc).
     */
    suspend fun getAllPending(): List<com.sona.ai.sync.PendingRequestEntry> {
        return pendingRequests.value
            .sortedWith(compareByDescending<PendingRequestRecord> { it.priority }.thenBy { it.timestamp })
            .map { record ->
                com.sona.ai.sync.PendingRequestEntry(
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
    fun observeCount(): Flow<Int> {
        return pendingRequests.map { it.size }
    }

    /**
     * Deletes a pending request by ID (marks it complete).
     */
    suspend fun delete(id: String) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            removeAll { it.id == id }
        }
    }

    /**
     * Increments retry count for a failed request.
     */
    suspend fun incrementRetry(id: String) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            val index = indexOfFirst { it.id == id }
            if (index >= 0) {
                set(index, get(index).copy(retryCount = get(index).retryCount + 1))
            }
        }
    }

    /**
     * Removes requests that have exceeded the maximum retry count.
     */
    suspend fun deleteExceededRetries(maxRetries: Int) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            removeAll { it.retryCount >= maxRetries }
        }
    }

    /**
     * Clears all pending requests.
     */
    suspend fun clearAll() {
        pendingRequests.value = mutableListOf()
    }
}
