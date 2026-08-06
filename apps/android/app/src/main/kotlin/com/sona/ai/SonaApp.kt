package com.sona.ai

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Sona AI OS - Android Application entry point.
 *
 * Uses Hilt for dependency injection across all feature modules.
 */
@HiltAndroidApp
class SonaApp : Application() {

    override fun onCreate() {
        super.onCreate()
        // Initialize app-level dependencies
    }
}
