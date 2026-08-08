package com.sona.ai.notifications

import android.annotation.SuppressLint
import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.sona.ai.MainActivity
import com.sona.ai.R
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Manages notification channels and displays notifications for Sona AI.
 * Handles different notification types: chat replies, agent completions,
 * memory updates, and sync status.
 */
@Singleton
class SonaNotificationManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    companion object {
        const val CHANNEL_CHAT = "sona_chat"
        const val CHANNEL_AGENTS = "sona_agents"
        const val CHANNEL_MEMORY = "sona_memory"
        const val CHANNEL_SYNC = "sona_sync"

        private const val NOTIFICATION_ID_CHAT = 1001
        private const val NOTIFICATION_ID_AGENT = 2001
        private const val NOTIFICATION_ID_MEMORY = 3001
        private const val NOTIFICATION_ID_SYNC = 4001
    }

    /**
     * Creates all notification channels. Should be called at app startup.
     */
    fun createNotificationChannels() {
        val channels = listOf(
            NotificationChannel(
                CHANNEL_CHAT,
                "Chat Messages",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notifications for new AI chat responses"
            },
            NotificationChannel(
                CHANNEL_AGENTS,
                "Agent Updates",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifications for AI agent execution status"
            },
            NotificationChannel(
                CHANNEL_MEMORY,
                "Memory Updates",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Notifications when Sona learns something new"
            },
            NotificationChannel(
                CHANNEL_SYNC,
                "Sync Status",
                NotificationManager.IMPORTANCE_MIN
            ).apply {
                description = "Background sync notifications"
            }
        )

        val notificationManager = context.getSystemService(NotificationManager::class.java)
        channels.forEach { notificationManager.createNotificationChannel(it) }
    }

    /**
     * Shows a chat response notification.
     */
    fun showChatNotification(title: String, message: String) {
        showNotification(
            channelId = CHANNEL_CHAT,
            notificationId = NOTIFICATION_ID_CHAT,
            title = title,
            message = message
        )
    }

    /**
     * Shows an agent completion notification.
     */
    fun showAgentNotification(agentName: String, status: String) {
        showNotification(
            channelId = CHANNEL_AGENTS,
            notificationId = NOTIFICATION_ID_AGENT,
            title = "Agent: $agentName",
            message = status
        )
    }

    /**
     * Shows a memory update notification.
     */
    fun showMemoryNotification(content: String) {
        showNotification(
            channelId = CHANNEL_MEMORY,
            notificationId = NOTIFICATION_ID_MEMORY,
            title = "New Memory",
            message = content
        )
    }

    /**
     * Shows a sync status notification.
     */
    fun showSyncNotification(message: String) {
        showNotification(
            channelId = CHANNEL_SYNC,
            notificationId = NOTIFICATION_ID_SYNC,
            title = "Sync",
            message = message
        )
    }

    @SuppressLint("MissingPermission")
    private fun showNotification(
        channelId: String,
        notificationId: Int,
        title: String,
        message: String
    ) {
        if (!hasNotificationPermission()) return

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        if (hasNotificationPermission()) {
            NotificationManagerCompat.from(context).notify(notificationId, notification)
        }
    }

    private fun hasNotificationPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }
}
