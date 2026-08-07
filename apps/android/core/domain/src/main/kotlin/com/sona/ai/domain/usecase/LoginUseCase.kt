package com.sona.ai.domain.usecase

import com.sona.ai.domain.model.UserProfile
import com.sona.ai.domain.repository.AuthRepository
import javax.inject.Inject

/**
 * Use case for authenticating a user.
 */
class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {

    /**
     * Authenticates user with email and password.
     *
     * @param email The user's email address.
     * @param password The user's password.
     * @return The authenticated user's profile.
     * @throws IllegalArgumentException if email or password is blank.
     */
    suspend fun execute(email: String, password: String): UserProfile {
        require(email.isNotBlank()) { "Email cannot be blank" }
        require(password.isNotBlank()) { "Password cannot be blank" }
        require(email.contains("@")) { "Invalid email format" }

        return authRepository.login(email, password)
    }
}
