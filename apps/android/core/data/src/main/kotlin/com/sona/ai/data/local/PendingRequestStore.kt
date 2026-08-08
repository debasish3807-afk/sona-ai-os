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

    private val pendingRequests = MutableStateFlow<MutableList<PendingRequestRecord>>(mutableListOf())

    data class PendingRequestRecord(
        val id: String,
        val type: String,
        val endpoint: String,
        val payload: String,
        val timestamp: Long,
        val retryCount: Int = 0,
        val priority: Int = 0
    )

    suspend fun insert(record: PendingRequestRecord) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply { add(record) }
    }

    suspend fun getAllPending(): List<PendingRequestRecord> {
        return pendingRequests.value
            .sortedWith(compareByDescending<PendingRequestRecord> { it.priority }.thenBy { it.timestamp })
    }

    fun observeCount(): Flow<Int> {
        return pendingRequests.map { it.size }
    }

    suspend fun delete(id: String) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            removeAll { it.id == id }
        }
    }

    suspend fun incrementRetry(id: String) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            val index = indexOfFirst { it.id == id }
            if (index >= 0) {
                set(index, get(index).copy(retryCount = get(index).retryCount + 1))
            }
        }
    }

    suspend fun deleteExceededRetries(maxRetries: Int) {
        pendingRequests.value = pendingRequests.value.toMutableList().apply {
            removeAll { it.retryCount >= maxRetries }
        }
    }

    suspend fun clearAll() {
        pendingRequests.value = mutableListOf()
    }
}
