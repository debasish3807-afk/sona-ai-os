package com.sona.ai.performance

import android.content.Context
import android.os.PowerManager
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BatteryOptimizer @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager

    fun isInPowerSaveMode(): Boolean = powerManager.isPowerSaveMode

    fun shouldReduceWork(): Boolean = isInPowerSaveMode()

    fun getRecommendedSyncInterval(): Long =
        if (isInPowerSaveMode()) 60 * 60 * 1000L else 15 * 60 * 1000L // 60min vs 15min
}
