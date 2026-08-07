package com.sona.ai.domain.repository

import com.sona.ai.domain.model.UserProfile
import kotlinx.coroutines.flow.Flow

/**
 * Repository interface for authentication operations.
 */
interface AuthRepository {

    /**
     * Authenticates user with email and password.
     */
    suspend fun login(email: String, password: String): UserProfile

    /**
     * Registers a new user account.
     */
    suspend fun register(name: String, email: String, password: String): UserProfile

    /**
     * Logs out the current user and clears tokens.
     */
    suspend fun logout()

    /**
     * Gets the currently authenticated user profile.
     */
    fun getCurrentUser(): Flow<UserProfile?>

    /**
     * Returns whether the user is currently authenticated.
     */
    suspend fun isAuthenticated(): Boolean

    /**
     * Gets the stored authentication token.
     */
    suspend fun getToken(): String?
}
