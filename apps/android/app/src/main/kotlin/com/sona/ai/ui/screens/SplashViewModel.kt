package com.sona.ai.ui.screens

import androidx.lifecycle.ViewModel
import com.sona.ai.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

/**
 * ViewModel for the Splash screen.
 * Checks authentication state to determine navigation target.
 */
@HiltViewModel
class SplashViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    /**
     * Checks if the user is currently authenticated.
     */
    suspend fun checkAuth(): Boolean {
        return try {
            authRepository.isAuthenticated()
        } catch (_: Exception) {
            false
        }
    }
}
