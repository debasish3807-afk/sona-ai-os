package com.sona.ai.features.communication.notifications

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationListenerBridge @Inject constructor(
    private val intelligence: NotificationIntelligence
) {
    fun onNotificationPosted(packageName: String, title: String, content: String) {
        val priority = intelligence.classifyPriority(title, content)
        intelligence.addNotification(
            NotificationItem(
                id = System.currentTimeMillis().toString(),
                app = packageName,
                title = title,
                content = content,
                priority = priority,
                timestamp = System.currentTimeMillis()
            )
        )
    }

    fun onNotificationRemoved(id: String) {
        // Track dismissed notifications for learning user preferences
    }
}
