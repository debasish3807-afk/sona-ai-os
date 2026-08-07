package com.sona.ai.features.communication.notifications

import javax.inject.Inject
import javax.inject.Singleton

data class NotificationItem(
    val id: String,
    val app: String,
    val title: String,
    val content: String,
    val priority: NotificationPriority,
    val timestamp: Long
)

enum class NotificationPriority { CRITICAL, HIGH, MEDIUM, LOW, SPAM }

@Singleton
class NotificationIntelligence @Inject constructor() {
    private val notifications = mutableListOf<NotificationItem>()

    fun addNotification(item: NotificationItem) {
        notifications.add(item)
    }

    fun getUnreadCount(): Int = notifications.size

    fun classifyPriority(title: String, content: String): NotificationPriority = when {
        content.contains("urgent", ignoreCase = true) ||
            content.contains("emergency", ignoreCase = true) -> NotificationPriority.CRITICAL
        content.contains("important", ignoreCase = true) ||
            content.contains("action required", ignoreCase = true) -> NotificationPriority.HIGH
        content.contains("promotion", ignoreCase = true) ||
            content.contains("deal", ignoreCase = true) -> NotificationPriority.LOW
        content.contains("unsubscribe", ignoreCase = true) ||
            content.contains("offer expires", ignoreCase = true) -> NotificationPriority.SPAM
        else -> NotificationPriority.MEDIUM
    }

    fun generateSummary(): String {
        if (notifications.isEmpty()) return "No new notifications."
        val grouped = notifications.groupBy { it.app }
        return buildString {
            grouped.forEach { (app, items) ->
                append("$app: ${items.size} notification(s). ")
                items.take(2).forEach { append("\"${it.title}\". ") }
                append("\n")
            }
        }
    }

    fun getGrouped(): Map<String, List<NotificationItem>> = notifications.groupBy { it.app }
}
