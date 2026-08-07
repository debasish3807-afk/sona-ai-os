package com.sona.ai.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.sona.ai.notifications.SonaNotificationManager
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * WorkManager worker that handles periodic synchronization.
 * Processes pending offline requests and syncs local data with the server.
 */
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val pendingRequestQueue: PendingRequestQueue,
    private val notificationManager: SonaNotificationManager
) : CoroutineWorker(context, workerParams) {

    companion object {
        private const val MAX_RETRIES = 5
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            // 1. Purge expired requests
            pendingRequestQueue.purgeExpiredRequests(MAX_RETRIES)

            // 2. Get all pending requests
            val pendingRequests = pendingRequestQueue.getPendingRequests()

            if (pendingRequests.isEmpty()) {
                return@withContext Result.success()
            }

            // 3. Process each pending request
            var successCount = 0
            var failureCount = 0

            for (request in pendingRequests) {
                try {
                    syncRequest(request)
                    pendingRequestQueue.markCompleted(request.id)
                    successCount++
                } catch (e: Exception) {
                    pendingRequestQueue.markRetry(request.id)
                    failureCount++
                }
            }

            // 4. Notify user of sync results if significant
            if (successCount > 0) {
                notificationManager.showSyncNotification(
                    "Synced $successCount pending request(s)"
                )
            }

            if (failureCount > 0) {
                return@withContext Result.retry()
            }

            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    /**
     * Processes a single pending request by sending it to the server.
     */
    private suspend fun syncRequest(request: PendingRequestEntry) {
        // Route request based on type
        when (request.type) {
            RequestType.CHAT_MESSAGE.name -> syncChatMessage(request)
            RequestType.FILE_UPLOAD.name -> syncFileUpload(request)
            RequestType.MEMORY_CREATE.name -> syncMemoryCreate(request)
            RequestType.MEMORY_DELETE.name -> syncMemoryDelete(request)
            RequestType.AGENT_EXECUTE.name -> syncAgentExecute(request)
            else -> throw IllegalArgumentException("Unknown request type: ${request.type}")
        }
    }

    private suspend fun syncChatMessage(request: PendingRequestEntry) {
        // Implementation would use ChatRepository to send the message
        // For now, this is a placeholder for the sync logic
    }

    private suspend fun syncFileUpload(request: PendingRequestEntry) {
        // Implementation would use FileUploadApi to upload the file
    }

    private suspend fun syncMemoryCreate(request: PendingRequestEntry) {
        // Implementation would use MemoryRepository to create memory
    }

    private suspend fun syncMemoryDelete(request: PendingRequestEntry) {
        // Implementation would use MemoryRepository to delete memory
    }

    private suspend fun syncAgentExecute(request: PendingRequestEntry) {
        // Implementation would use AgentApi to execute agent
    }
}
