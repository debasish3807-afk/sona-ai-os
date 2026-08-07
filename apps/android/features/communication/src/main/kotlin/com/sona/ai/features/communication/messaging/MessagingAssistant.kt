package com.sona.ai.features.communication.messaging

import javax.inject.Inject
import javax.inject.Singleton

data class Conversation(
    val contactName: String,
    val lastMessage: String,
    val timestamp: Long,
    val unreadCount: Int = 0
)

data class ReplySuggestion(val text: String, val tone: String)

data class ExtractedReminder(val text: String, val dueDate: String = "")

data class ExtractedTask(val title: String, val priority: String = "medium")

@Singleton
class MessagingAssistant @Inject constructor() {
    private val conversations = mutableListOf<Conversation>()

    fun addConversation(conv: Conversation) {
        conversations.add(conv)
    }

    fun getConversationCount(): Int = conversations.size

    fun generateReplySuggestions(message: String): List<ReplySuggestion> = listOf(
        ReplySuggestion("Sure, sounds good!", "positive"),
        ReplySuggestion("Let me check and get back to you.", "neutral"),
        ReplySuggestion("Thanks for letting me know.", "acknowledgment")
    )

    fun extractReminders(messages: List<String>): List<ExtractedReminder> =
        messages.filter {
            it.contains("remind", ignoreCase = true) ||
                it.contains("don't forget", ignoreCase = true)
        }.map { ExtractedReminder(it) }

    fun extractTasks(messages: List<String>): List<ExtractedTask> =
        messages.filter {
            it.contains("todo", ignoreCase = true) ||
                it.contains("need to", ignoreCase = true) ||
                it.contains("should", ignoreCase = true)
        }.map { ExtractedTask(it) }

    fun detectCalendarEvents(messages: List<String>): List<String> =
        messages.filter {
            it.contains("meeting", ignoreCase = true) ||
                it.contains("appointment", ignoreCase = true) ||
                it.contains("tomorrow at", ignoreCase = true)
        }

    fun generateSummary(): String =
        if (conversations.isEmpty()) "No recent conversations."
        else "${conversations.size} conversation(s). Most recent: ${conversations.last().contactName} - \"${conversations.last().lastMessage}\""
}
