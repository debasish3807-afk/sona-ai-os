package com.sona.ai.service

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Controls the notification UI for the voice assistant foreground service.
 * Provides media-style notification with action buttons for controlling
 * the assistant (stop, mute, etc.).
 */
@Singleton
class VoiceNotificationController @Inject constructor(
    @ApplicationContext private val context: Context
) {

    /**
     * Builds a notification with action controls for the voice assistant service.
     */
    fun buildControls(): NotificationCompat.Builder {
        val stopIntent = Intent(context, VoiceAssistantService::class.java).apply {
            action = VoiceAssistantService.ACTION_STOP
        }
        val stopPending = PendingIntent.getService(
            context,
            0,
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(context, VoiceAssistantService.CHANNEL_ID)
            .setContentTitle("Sona AI Assistant")
            .setContentText("Listening for commands...")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .addAction(
                android.R.drawable.ic_delete,
                "Stop",
                stopPending
            )
            .setOngoing(true)
    }

    /**
     * Builds a notification indicating the assistant is processing a command.
     */
    fun buildProcessingNotification(): NotificationCompat.Builder {
        return NotificationCompat.Builder(context, VoiceAssistantService.CHANNEL_ID)
            .setContentTitle("Sona AI Assistant")
            .setContentText("Processing your request...")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
    }

    /**
     * Builds a notification indicating the assistant is speaking.
     */
    fun buildSpeakingNotification(text: String): NotificationCompat.Builder {
        val stopIntent = Intent(context, VoiceAssistantService::class.java).apply {
            action = VoiceAssistantService.ACTION_STOP
        }
        val stopPending = PendingIntent.getService(
            context,
            0,
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(context, VoiceAssistantService.CHANNEL_ID)
            .setContentTitle("Sona AI Speaking")
            .setContentText(text.take(100))
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .addAction(
                android.R.drawable.ic_delete,
                "Stop",
                stopPending
            )
            .setOngoing(true)
    }
}
