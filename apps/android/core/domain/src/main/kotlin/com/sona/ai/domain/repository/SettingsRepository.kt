package com.sona.ai.domain.repository

import com.sona.ai.domain.model.AppSettings
import com.sona.ai.domain.model.AppTheme
import kotlinx.coroutines.flow.Flow

/**
 * Repository interface for application settings.
 */
interface SettingsRepository {

    /**
     * Gets the current application settings as a Flow.
     */
    fun getSettings(): Flow<AppSettings>

    /**
     * Updates the application theme.
     */
    suspend fun updateTheme(theme: AppTheme)

    /**
     * Updates the API URL.
     */
    suspend fun updateApiUrl(url: String)

    /**
     * Updates the AI model name.
     */
    suspend fun updateModel(model: String)

    /**
     * Updates the temperature setting.
     */
    suspend fun updateTemperature(temperature: Float)

    /**
     * Updates streaming enabled preference.
     */
    suspend fun updateStreamingEnabled(enabled: Boolean)

    /**
     * Resets all settings to defaults.
     */
    suspend fun resetToDefaults()
}
