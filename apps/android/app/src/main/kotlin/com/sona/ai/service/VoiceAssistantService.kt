package com.sona.ai.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.sona.ai.features.voice.assistant.VoiceAssistant
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Foreground service that keeps the voice assistant active in the background.
 * Runs as a foreground service with a persistent notification to maintain
 * continuous listening capability.
 */
@AndroidEntryPoint
class VoiceAssistantService : Service() {

    @Inject
    lateinit var voiceAssistant: VoiceAssistant

    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification("Sona is listening..."))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startAssistant()
            ACTION_STOP -> stopSelf()
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private fun startAssistant() {
        scope.launch {
            voiceAssistant.startContinuousMode()
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Voice Assistant",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Notification channel for Sona voice assistant service"
        }
        val notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannel(channel)
    }

    private fun buildNotification(text: String): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Sona AI")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .build()

    companion object {
        const val CHANNEL_ID = "voice_assistant"
        const val NOTIFICATION_ID = 1001
        const val ACTION_START = "com.sona.ai.service.START"
        const val ACTION_STOP = "com.sona.ai.service.STOP"
    }
}
