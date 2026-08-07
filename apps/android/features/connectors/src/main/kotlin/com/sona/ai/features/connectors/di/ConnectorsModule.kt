package com.sona.ai.features.connectors.di

import com.sona.ai.features.connectors.github.GitHubConnector
import com.sona.ai.features.connectors.google.GoogleConnector
import com.sona.ai.features.connectors.runtime.ConnectorRegistry
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt DI module for the Connectors feature.
 * Provides the ConnectorRegistry pre-configured with all
 * available connector implementations.
 */
@Module
@InstallIn(SingletonComponent::class)
object ConnectorsModule {

    @Provides
    @Singleton
    fun provideConnectorRegistry(
        github: GitHubConnector,
        google: GoogleConnector
    ): ConnectorRegistry {
        return ConnectorRegistry().apply {
            register(github)
            register(google)
        }
    }
}
