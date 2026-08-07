package com.sona.ai.di

import com.sona.ai.domain.repository.AuthRepository
import com.sona.ai.domain.repository.ChatRepository
import com.sona.ai.domain.repository.MemoryRepository
import com.sona.ai.domain.usecase.GetMemoriesUseCase
import com.sona.ai.domain.usecase.LoginUseCase
import com.sona.ai.domain.usecase.SendMessageUseCase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module providing use case instances.
 */
@Module
@InstallIn(SingletonComponent::class)
object UseCaseModule {

    @Provides
    @Singleton
    fun provideSendMessageUseCase(
        chatRepository: ChatRepository
    ): SendMessageUseCase {
        return SendMessageUseCase(chatRepository)
    }

    @Provides
    @Singleton
    fun provideLoginUseCase(
        authRepository: AuthRepository
    ): LoginUseCase {
        return LoginUseCase(authRepository)
    }

    @Provides
    @Singleton
    fun provideGetMemoriesUseCase(
        memoryRepository: MemoryRepository
    ): GetMemoriesUseCase {
        return GetMemoriesUseCase(memoryRepository)
    }
}
