package com.sona.ai.features.overlay

import android.content.Context
import android.content.Intent
import android.provider.Settings
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BubbleController @Inject constructor(
    @ApplicationContext private val context: Context
) {

    fun canShowOverlay(): Boolean = Settings.canDrawOverlays(context)

    fun start() {
        if (canShowOverlay()) {
            context.startForegroundService(
                Intent(context, FloatingBubbleService::class.java)
            )
        }
    }

    fun stop() {
        context.stopService(Intent(context, FloatingBubbleService::class.java))
    }
}
