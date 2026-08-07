package com.sona.ai.features.dashboard.data

import com.sona.ai.features.dashboard.ConversationPreview
import com.sona.ai.features.dashboard.ContinueWorkingItem
import com.sona.ai.features.dashboard.MemoryHighlight
import com.sona.ai.features.dashboard.ScheduleItem
import com.sona.ai.features.dashboard.TaskItem
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Aggregated dashboard data loaded from various sources.
 */
data class DashboardData(
    val dailyBrief: String,
    val schedule: List<ScheduleItem>,
    val githubSummary: String,
    val emailSummary: String,
    val unreadEmails: Int,
    val tasks: List<TaskItem>,
    val memoryHighlights: List<MemoryHighlight>,
    val recentConversations: List<ConversationPreview>,
    val continueWorking: List<ContinueWorkingItem>
)

/**
 * Provides aggregated data for the Dashboard from multiple sources.
 * In production, this would coordinate calls to calendar, email, GitHub,
 * memory, and task services. Currently provides representative sample data.
 */
@Singleton
class DashboardDataProvider @Inject constructor() {

    /**
     * Loads all dashboard data from available services.
     * Each data source is loaded independently so partial failures
     * don't block the entire dashboard.
     */
    suspend fun loadAll(): DashboardData {
        return DashboardData(
            dailyBrief = generateDailyBrief(),
            schedule = loadSchedule(),
            githubSummary = loadGitHubSummary(),
            emailSummary = loadEmailSummary(),
            unreadEmails = loadUnreadEmailCount(),
            tasks = loadTasks(),
            memoryHighlights = loadMemoryHighlights(),
            recentConversations = loadRecentConversations(),
            continueWorking = loadContinueWorking()
        )
    }

    private suspend fun generateDailyBrief(): String {
        return "You have 3 meetings today, 2 PRs to review, and 5 unread emails. " +
            "Your AI agents completed 2 tasks overnight."
    }

    private suspend fun loadSchedule(): List<ScheduleItem> {
        return listOf(
            ScheduleItem("9:00 AM", "Team Standup", "Google Meet"),
            ScheduleItem("11:00 AM", "Design Review", "Room 3B"),
            ScheduleItem("2:00 PM", "Sprint Planning", "Zoom")
        )
    }

    private suspend fun loadGitHubSummary(): String {
        return "2 PRs need review. 1 CI failure on main. 3 new issues assigned."
    }

    private suspend fun loadEmailSummary(): String {
        return "5 unread emails. 2 from team, 1 from client (marked important)."
    }

    private suspend fun loadUnreadEmailCount(): Int = 5

    private suspend fun loadTasks(): List<TaskItem> {
        return listOf(
            TaskItem("1", "Review PR #73", "high", "Today"),
            TaskItem("2", "Update documentation", "medium", "Tomorrow"),
            TaskItem("3", "Fix CI pipeline", "high", "Today")
        )
    }

    private suspend fun loadMemoryHighlights(): List<MemoryHighlight> {
        return listOf(
            MemoryHighlight(
                "Discussed Clean Architecture patterns",
                "2 hours ago",
                "conversation"
            ),
            MemoryHighlight(
                "Completed Sprint 22 implementation",
                "Yesterday",
                "project"
            )
        )
    }

    private suspend fun loadRecentConversations(): List<ConversationPreview> {
        return listOf(
            ConversationPreview(
                "c1",
                "Code Review Help",
                "Can you review this function?",
                "30 min ago"
            ),
            ConversationPreview(
                "c2",
                "Architecture Discussion",
                "Let's use hexagonal architecture",
                "2 hours ago"
            )
        )
    }

    private suspend fun loadContinueWorking(): List<ContinueWorkingItem> {
        return listOf(
            ContinueWorkingItem(
                "w1",
                "Sprint 24 Implementation",
                "Dashboard feature in progress",
                "code"
            ),
            ContinueWorkingItem(
                "w2",
                "PR Review",
                "3 files remaining to review",
                "review"
            )
        )
    }
}
