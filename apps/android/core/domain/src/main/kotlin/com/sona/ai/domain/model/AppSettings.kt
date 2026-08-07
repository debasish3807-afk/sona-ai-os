package com.sona.ai.domain.model

/**
 * Application-level settings.
 */
data class AppSettings(
    val theme: AppTheme = AppTheme.SYSTEM,
    val apiUrl: String = "https://api.sona.ai",
    val model: String = "sona-v1",
    val temperature: Float = 0.7f,
    val maxTokens: Int = 4096,
    val streamingEnabled: Boolean = true
)

/**
 * Application theme options.
 */
enum class AppTheme {
    LIGHT,
    DARK,
    SYSTEM
}
