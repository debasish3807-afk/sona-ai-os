package com.sona.ai.features.settings

import com.sona.ai.domain.model.AppSettings
import com.sona.ai.domain.model.AppTheme

/**
 * UI state for the settings screen.
 */
data class SettingsState(
    val isLoading: Boolean = true,
    val settings: AppSettings = AppSettings(),
    val error: String? = null,
    val isSaving: Boolean = false,
    val userName: String = "",
    val userEmail: String = ""
)

/**
 * One-time events for the settings screen.
 */
sealed interface SettingsEvent {
    data class ShowMessage(val message: String) : SettingsEvent
    data object SettingsSaved : SettingsEvent
    data object LoggedOut : SettingsEvent
}
