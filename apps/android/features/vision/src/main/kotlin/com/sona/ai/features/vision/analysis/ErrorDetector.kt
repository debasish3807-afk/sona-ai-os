package com.sona.ai.features.vision.analysis

import android.net.Uri
import com.sona.ai.features.vision.AnalysisOutput
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Specialized analyzer for detecting errors in screenshots.
 * Uses the base VisionAnalyzer and adds error-specific detection logic.
 */
@Singleton
class ErrorDetector @Inject constructor(
    private val analyzer: VisionAnalyzer
) {
    /**
     * Detect errors visible in a screenshot (e.g., error dialogs, stack traces, red highlights).
     *
     * @param imageUri URI pointing to the screenshot to analyze
     * @return [AnalysisOutput] with error detection results and suggestions
     */
    suspend fun detectErrors(imageUri: Uri): AnalysisOutput {
        val base = analyzer.analyze(imageUri)
        return base.copy(
            category = "error_detection",
            suggestions = base.suggestions + "Check highlighted error messages in the screenshot"
        )
    }

    /**
     * Detect compilation errors in code screenshots.
     */
    suspend fun detectCompilationErrors(imageUri: Uri): AnalysisOutput {
        val base = analyzer.analyze(imageUri)
        return base.copy(
            category = "compilation_error",
            suggestions = base.suggestions + listOf(
                "Review syntax errors highlighted in red",
                "Check import statements for missing dependencies"
            )
        )
    }

    /**
     * Detect runtime errors or crashes in app screenshots.
     */
    suspend fun detectRuntimeErrors(imageUri: Uri): AnalysisOutput {
        val base = analyzer.analyze(imageUri)
        return base.copy(
            category = "runtime_error",
            suggestions = base.suggestions + listOf(
                "Check the stack trace for the root cause",
                "Review null pointer or type casting issues"
            )
        )
    }
}
