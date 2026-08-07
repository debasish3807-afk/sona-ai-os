package com.sona.ai.features.beta

import com.sona.ai.features.beta.diagnostics.DeviceInfo
import javax.inject.Inject
import javax.inject.Singleton

data class FeedbackReport(
    val type: String,
    val description: String,
    val deviceInfo: DeviceInfo? = null,
    val logs: String? = null,
    val timestamp: Long = 0
)

@Singleton
class FeedbackRepository @Inject constructor() {
    private val reports = mutableListOf<FeedbackReport>()

    suspend fun submit(report: FeedbackReport) {
        reports.add(report)
    }

    fun getReports(): List<FeedbackReport> = reports.toList()
}
