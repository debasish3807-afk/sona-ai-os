package com.sona.ai.features.communication

data class CommunicationState(
    val unreadCount: Int = 0,
    val messageCount: Int = 0,
    val missedCalls: Int = 0,
    val unreadEmails: Int = 0,
    val contactInsights: Int = 0,
    val summary: String = "",
    val isLoading: Boolean = false
)
