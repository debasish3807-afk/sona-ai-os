package com.sona.ai.features.dashboard

/**
 * Represents a scheduled event/meeting for the day.
 */
data class ScheduleItem(
    val time: String,
    val title: String,
    val location: String = "",
    val color: Long = 0xFF6200EE
)

/**
 * Represents a task/todo item.
 */
data class TaskItem(
    val id: String,
    val title: String,
    val priority: String,
    val dueDate: String = "",
    val completed: Boolean = false
)

/**
 * Represents a memory highlight from Sona's memory system.
 */
data class MemoryHighlight(
    val content: String,
    val timeAgo: String,
    val type: String
)

/**
 * Preview of a recent conversation with the AI.
 */
data class ConversationPreview(
    val id: String,
    val title: String,
    val lastMessage: String,
    val timeAgo: String
)

/**
 * Represents an item the user can continue working on.
 */
data class ContinueWorkingItem(
    val id: String,
    val title: String,
    val context: String,
    val type: String
)

/**
 * Complete UI state for the Dashboard screen.
 * Uses immutable data classes to support StateFlow-based state management.
 */
data class DashboardState(
    val greeting: String = "Good morning",
    val dailyBrief: String = "",
    val scheduleItems: List<ScheduleItem> = emptyList(),
    val githubSummary: String = "",
    val emailSummary: String = "",
    val unreadEmails: Int = 0,
    val tasks: List<TaskItem> = emptyList(),
    val memoryHighlights: List<MemoryHighlight> = emptyList(),
    val recentConversations: List<ConversationPreview> = emptyList(),
    val continueWorking: List<ContinueWorkingItem> = emptyList(),
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false
)
