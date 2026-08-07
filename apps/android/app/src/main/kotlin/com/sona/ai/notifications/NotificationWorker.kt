package com.sona.ai.notifications

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

/**
 * Background worker for handling notifications.
 * Processes incoming push notifications and triggers appropriate UI updates.
 */
@HiltWorker
class NotificationWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val notificationManager: SonaNotificationManager
) : CoroutineWorker(context, workerParams) {

    companion object {
        const val KEY_NOTIFICATION_TYPE = "notification_type"
        const val KEY_TITLE = "title"
        const val KEY_MESSAGE = "message"
        const val KEY_AGENT_NAME = "agent_name"
        const val KEY_AGENT_STATUS = "agent_status"

        const val TYPE_CHAT = "chat"
        const val TYPE_AGENT = "agent"
        const val TYPE_MEMORY = "memory"
        const val TYPE_SYNC = "sync"
    }

    override suspend fun doWork(): Result {
        val type = inputData.getString(KEY_NOTIFICATION_TYPE) ?: return Result.failure()
        val title = inputData.getString(KEY_TITLE) ?: "Sona AI"
        val message = inputData.getString(KEY_MESSAGE) ?: ""

        when (type) {
            TYPE_CHAT -> {
                notificationManager.showChatNotification(title, message)
            }
            TYPE_AGENT -> {
                val agentName = inputData.getString(KEY_AGENT_NAME) ?: "Agent"
                val status = inputData.getString(KEY_AGENT_STATUS) ?: "Complete"
                notificationManager.showAgentNotification(agentName, status)
            }
            TYPE_MEMORY -> {
                notificationManager.showMemoryNotification(message)
            }
            TYPE_SYNC -> {
                notificationManager.showSyncNotification(message)
            }
            else -> return Result.failure()
        }

        return Result.success()
    }
}
