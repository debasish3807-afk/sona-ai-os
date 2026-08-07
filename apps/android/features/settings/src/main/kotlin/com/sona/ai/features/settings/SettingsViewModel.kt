package com.sona.ai.features.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.domain.model.AppTheme
import com.sona.ai.domain.repository.AuthRepository
import com.sona.ai.domain.repository.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Settings screen.
 * Manages app settings and user profile state.
 */
@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _state = MutableStateFlow(SettingsState())
    val state: StateFlow<SettingsState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<SettingsEvent>()
    val events: SharedFlow<SettingsEvent> = _events.asSharedFlow()

    init {
        loadSettings()
    }

    private fun loadSettings() {
        settingsRepository.getSettings()
            .combine(authRepository.getCurrentUser()) { settings, user ->
                _state.update {
                    it.copy(
                        isLoading = false,
                        settings = settings,
                        userName = user?.name ?: "",
                        userEmail = user?.email ?: ""
                    )
                }
            }
            .catch { e ->
                _state.update {
                    it.copy(isLoading = false, error = e.message)
                }
            }
            .launchIn(viewModelScope)
    }

    fun updateTheme(theme: AppTheme) {
        viewModelScope.launch {
            settingsRepository.updateTheme(theme)
            _state.update { it.copy(settings = it.settings.copy(theme = theme)) }
        }
    }

    fun updateApiUrl(url: String) {
        viewModelScope.launch {
            settingsRepository.updateApiUrl(url)
            _state.update { it.copy(settings = it.settings.copy(apiUrl = url)) }
        }
    }

    fun updateModel(model: String) {
        viewModelScope.launch {
            settingsRepository.updateModel(model)
            _state.update { it.copy(settings = it.settings.copy(model = model)) }
        }
    }

    fun updateTemperature(temperature: Float) {
        viewModelScope.launch {
            settingsRepository.updateTemperature(temperature)
            _state.update { it.copy(settings = it.settings.copy(temperature = temperature)) }
        }
    }

    fun updateStreaming(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepository.updateStreamingEnabled(enabled)
            _state.update { it.copy(settings = it.settings.copy(streamingEnabled = enabled)) }
        }
    }

    fun resetToDefaults() {
        viewModelScope.launch {
            settingsRepository.resetToDefaults()
            _events.emit(SettingsEvent.ShowMessage("Settings reset to defaults"))
        }
    }

    fun logout() {
        viewModelScope.launch {
            try {
                authRepository.logout()
                _events.emit(SettingsEvent.LoggedOut)
            } catch (e: Exception) {
                _events.emit(SettingsEvent.ShowMessage("Logout failed: ${e.message}"))
            }
        }
    }
}
