package com.sona.ai.features.dashboard.di

import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/**
 * Hilt DI module for the Dashboard feature.
 * DashboardDataProvider is automatically provided via @Inject constructor.
 * This module exists for future bindings as the dashboard grows.
 */
@Module
@InstallIn(SingletonComponent::class)
object DashboardModule
