package com.sona.ai.accessibility

import android.content.Context
import android.view.accessibility.AccessibilityManager
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AccessibilityConfig @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val accessibilityManager =
        context.getSystemService(Context.ACCESSIBILITY_SERVICE) as AccessibilityManager

    fun isTalkBackEnabled(): Boolean = accessibilityManager.isEnabled

    fun isHighContrastEnabled(): Boolean = false // Check system setting

    fun getRecommendedFontScale(): Float = context.resources.configuration.fontScale

    fun shouldUseReducedMotion(): Boolean = false // Respect user preference
}
