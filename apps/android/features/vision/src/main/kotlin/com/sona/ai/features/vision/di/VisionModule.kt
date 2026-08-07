package com.sona.ai.features.vision.di

import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/**
 * Hilt dependency injection module for the Vision AI feature.
 *
 * All vision processors (OcrEngine, VisionAnalyzer, DocumentProcessor, etc.)
 * are constructor-injected via @Inject and @Singleton annotations,
 * so no explicit @Provides methods are needed here.
 *
 * This module serves as the Hilt registration point for the vision feature's
 * dependency graph within the SingletonComponent.
 */
@Module
@InstallIn(SingletonComponent::class)
object VisionModule {
    // ML Kit recognizer and processors are constructor-injected via @Inject.
    // OcrEngine, PdfOcrProcessor, VisionAnalyzer, ErrorDetector,
    // DocumentProcessor, and TableParser all use @Singleton + @Inject constructor.
}
