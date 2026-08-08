package com.sona.ai.monitoring

import javax.inject.Inject
import javax.inject.Singleton

data class MonitoringMetrics(
    val crashFreeRate: Float = 99.9f,
    val activeUsers: Int = 0,
    val avgStartupMs: Long = 0,
    val avgMemoryMb: Long = 0,
    val syncFailures: Int = 0,
    val apiFailures: Int = 0,
    val avgAiLatencyMs: Long = 0
)

@Singleton
class ProductionMonitor @Inject constructor() {

    private var startupTime: Long = 0
    private var apiCalls = 0
    private var apiFailures = 0
    private var syncAttempts = 0
    private var syncFailures = 0

    fun recordStartup(durationMs: Long) {
        startupTime = durationMs
    }

    fun recordApiCall(success: Boolean, latencyMs: Long) {
        apiCalls++
        if (!success) apiFailures++
    }

    fun recordSync(success: Boolean) {
        syncAttempts++
        if (!success) syncFailures++
    }

    fun getMetrics(): MonitoringMetrics = MonitoringMetrics(
        crashFreeRate = if (apiCalls > 0) (1f - apiFailures.toFloat() / apiCalls) * 100 else 99.9f,
        avgStartupMs = startupTime,
        syncFailures = syncFailures,
        apiFailures = apiFailures
    )
}
