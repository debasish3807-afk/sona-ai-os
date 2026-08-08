package com.sona.ai.firebase

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RemoteConfigManager @Inject constructor() {

    private val defaults = mapOf(
        "voice_enabled" to true,
        "vision_enabled" to true,
        "max_message_length" to 10000L,
        "sync_interval_minutes" to 15L,
        "ai_model" to "llama3.2",
        "beta_features_enabled" to true
    )

    private val overrides = mutableMapOf<String, Any>()

    fun getBoolean(key: String): Boolean =
        (overrides[key] as? Boolean) ?: (defaults[key] as? Boolean) ?: false

    fun getLong(key: String): Long =
        (overrides[key] as? Long) ?: (defaults[key] as? Long) ?: 0L

    fun getString(key: String): String =
        (overrides[key] as? String) ?: (defaults[key] as? String) ?: ""

    fun setOverride(key: String, value: Any) {
        overrides[key] = value
    }

    suspend fun fetch() {
        // In production: FirebaseRemoteConfig.getInstance().fetchAndActivate()
        // This will pull latest feature flags from Firebase Remote Config
    }
}
