package com.sona.ai.di

import com.sona.ai.data.repository.AuthRepositoryImpl
import com.sona.ai.data.repository.ChatRepositoryImpl
import com.sona.ai.data.repository.MemoryRepositoryImpl
import com.sona.ai.data.repository.SettingsRepositoryImpl
import com.sona.ai.domain.repository.AuthRepository
import com.sona.ai.domain.repository.ChatRepository
import com.sona.ai.domain.repository.MemoryRepository
import com.sona.ai.domain.repository.SettingsRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module binding repository interfaces to their implementations.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindChatRepository(
        impl: ChatRepositoryImpl
    ): ChatRepository

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        impl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindMemoryRepository(
        impl: MemoryRepositoryImpl
    ): MemoryRepository

    @Binds
    @Singleton
    abstract fun bindSettingsRepository(
        impl: SettingsRepositoryImpl
    ): SettingsRepository
}
