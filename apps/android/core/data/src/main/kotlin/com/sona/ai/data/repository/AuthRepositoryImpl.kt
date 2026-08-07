package com.sona.ai.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import com.sona.ai.data.remote.SonaApi
import com.sona.ai.data.remote.dto.AuthRequestDto
import com.sona.ai.data.remote.dto.RegisterRequestDto
import com.sona.ai.domain.model.UserProfile
import com.sona.ai.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Implementation of [AuthRepository] using Retrofit and DataStore.
 */
@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val api: SonaApi,
    private val dataStore: DataStore<Preferences>
) : AuthRepository {

    private companion object {
        val KEY_USER_ID = stringPreferencesKey("user_id")
        val KEY_USER_NAME = stringPreferencesKey("user_name")
        val KEY_USER_EMAIL = stringPreferencesKey("user_email")
        val KEY_AUTH_TOKEN = stringPreferencesKey("auth_token")
        val KEY_AVATAR_URL = stringPreferencesKey("avatar_url")
    }

    override suspend fun login(email: String, password: String): UserProfile {
        val response = api.login(AuthRequestDto(email, password))
        val profile = UserProfile(
            id = response.userId,
            name = response.name,
            email = response.email,
            token = response.token,
            avatarUrl = response.avatarUrl
        )
        saveProfile(profile)
        return profile
    }

    override suspend fun register(name: String, email: String, password: String): UserProfile {
        val response = api.register(RegisterRequestDto(name, email, password))
        val profile = UserProfile(
            id = response.userId,
            name = response.name,
            email = response.email,
            token = response.token,
            avatarUrl = response.avatarUrl
        )
        saveProfile(profile)
        return profile
    }

    override suspend fun logout() {
        val token = getToken()
        token?.let {
            try {
                api.logout("Bearer $it")
            } catch (_: Exception) {
                // Ignore network errors on logout
            }
        }
        dataStore.edit { it.clear() }
    }

    override fun getCurrentUser(): Flow<UserProfile?> {
        return dataStore.data.map { prefs ->
            val id = prefs[KEY_USER_ID] ?: return@map null
            UserProfile(
                id = id,
                name = prefs[KEY_USER_NAME] ?: "",
                email = prefs[KEY_USER_EMAIL] ?: "",
                token = prefs[KEY_AUTH_TOKEN] ?: "",
                avatarUrl = prefs[KEY_AVATAR_URL] ?: ""
            )
        }
    }

    override suspend fun isAuthenticated(): Boolean {
        return getToken() != null
    }

    override suspend fun getToken(): String? {
        return dataStore.data.first()[KEY_AUTH_TOKEN]
    }

    private suspend fun saveProfile(profile: UserProfile) {
        dataStore.edit { prefs ->
            prefs[KEY_USER_ID] = profile.id
            prefs[KEY_USER_NAME] = profile.name
            prefs[KEY_USER_EMAIL] = profile.email
            prefs[KEY_AUTH_TOKEN] = profile.token
            prefs[KEY_AVATAR_URL] = profile.avatarUrl
        }
    }
}
