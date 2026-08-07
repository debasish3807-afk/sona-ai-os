package com.sona.ai.firebase

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FirebaseManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    var isCrashlyticsEnabled = true
        private set
    var isAnalyticsEnabled = false
        private set
    var isPerformanceEnabled = true
        private set

    fun initialize() {
        // Firebase.initialize(context) — requires google-services.json
        // Crashlytics, Analytics, and Performance will be initialized here
        // once Firebase is configured for the project
    }

    fun enableCrashlytics(enabled: Boolean) {
        isCrashlyticsEnabled = enabled
    }

    fun enableAnalytics(enabled: Boolean) {
        isAnalyticsEnabled = enabled
    }

    fun logEvent(name: String, params: Map<String, String> = emptyMap()) {
        if (isAnalyticsEnabled) {
            // FirebaseAnalytics.getInstance(context).logEvent(name, Bundle().apply {
            //     params.forEach { putString(it.key, it.value) }
            // })
        }
    }

    fun logError(tag: String, message: String, throwable: Throwable? = null) {
        if (isCrashlyticsEnabled) {
            // FirebaseCrashlytics.getInstance().log("[$tag] $message")
            // throwable?.let { FirebaseCrashlytics.getInstance().recordException(it) }
        }
    }

    fun setUserId(userId: String) {
        // FirebaseAnalytics.getInstance(context).setUserId(userId)
        // FirebaseCrashlytics.getInstance().setUserId(userId)
    }
}
