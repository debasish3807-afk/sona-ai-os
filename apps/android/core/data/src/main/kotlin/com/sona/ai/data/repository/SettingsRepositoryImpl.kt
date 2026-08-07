package com.sona.ai.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import com.sona.ai.domain.model.AppSettings
import com.sona.ai.domain.model.AppTheme
import com.sona.ai.domain.repository.SettingsRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Named
import javax.inject.Singleton

/**
 * Implementation of [SettingsRepository] using DataStore Preferences.
 */
@Singleton
class SettingsRepositoryImpl @Inject constructor(
    @Named("settings") private val dataStore: DataStore<Preferences>
) : SettingsRepository {

    private companion object {
        val KEY_THEME = stringPreferencesKey("settings_theme")
        val KEY_API_URL = stringPreferencesKey("settings_api_url")
        val KEY_MODEL = stringPreferencesKey("settings_model")
        val KEY_TEMPERATURE = floatPreferencesKey("settings_temperature")
        val KEY_STREAMING = booleanPreferencesKey("settings_streaming")
    }

    override fun getSettings(): Flow<AppSettings> {
        return dataStore.data.map { prefs ->
            AppSettings(
                theme = try {
                    AppTheme.valueOf(prefs[KEY_THEME] ?: AppTheme.SYSTEM.name)
                } catch (_: Exception) {
                    AppTheme.SYSTEM
                },
                apiUrl = prefs[KEY_API_URL] ?: "https://api.sona.ai",
                model = prefs[KEY_MODEL] ?: "sona-v1",
                temperature = prefs[KEY_TEMPERATURE] ?: 0.7f,
                streamingEnabled = prefs[KEY_STREAMING] ?: true
            )
        }
    }

    override suspend fun updateTheme(theme: AppTheme) {
        dataStore.edit { it[KEY_THEME] = theme.name }
    }

    override suspend fun updateApiUrl(url: String) {
        dataStore.edit { it[KEY_API_URL] = url }
    }

    override suspend fun updateModel(model: String) {
        dataStore.edit { it[KEY_MODEL] = model }
    }

    override suspend fun updateTemperature(temperature: Float) {
        dataStore.edit { it[KEY_TEMPERATURE] = temperature }
    }

    override suspend fun updateStreamingEnabled(enabled: Boolean) {
        dataStore.edit { it[KEY_STREAMING] = enabled }
    }

    override suspend fun resetToDefaults() {
        dataStore.edit { it.clear() }
    }
}
