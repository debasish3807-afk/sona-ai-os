package com.sona.ai.widget

import javax.inject.Inject
import javax.inject.Singleton

data class WidgetData(
    val greeting: String,
    val taskCount: Int,
    val nextEvent: String,
    val summary: String
)

@Singleton
class SonaWidgetProvider @Inject constructor() {

    fun getWidgetData(): WidgetData = WidgetData(
        greeting = "Good morning",
        taskCount = 3,
        nextEvent = "Team Standup at 9:00 AM",
        summary = "2 PRs to review, 5 unread emails"
    )
}
