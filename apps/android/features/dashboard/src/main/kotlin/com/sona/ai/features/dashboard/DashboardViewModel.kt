package com.sona.ai.features.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.features.dashboard.data.DashboardDataProvider
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalTime
import javax.inject.Inject

/**
 * ViewModel for the Dashboard screen.
 * Manages dashboard state and coordinates data loading from multiple sources.
 */
@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val dataProvider: DashboardDataProvider
) : ViewModel() {

    private val _state = MutableStateFlow(DashboardState())
    val state: StateFlow<DashboardState> = _state.asStateFlow()

    init {
        loadDashboard()
    }

    /**
     * Refreshes all dashboard data (triggered by pull-to-refresh).
     */
    fun refresh() {
        _state.update { it.copy(isRefreshing = true) }
        loadDashboard()
    }

    private fun loadDashboard() {
        viewModelScope.launch {
            val greeting = generateGreeting()
            val data = dataProvider.loadAll()
            _state.value = DashboardState(
                greeting = greeting,
                dailyBrief = data.dailyBrief,
                scheduleItems = data.schedule,
                githubSummary = data.githubSummary,
                emailSummary = data.emailSummary,
                unreadEmails = data.unreadEmails,
                tasks = data.tasks,
                memoryHighlights = data.memoryHighlights,
                recentConversations = data.recentConversations,
                continueWorking = data.continueWorking,
                isLoading = false,
                isRefreshing = false
            )
        }
    }

    /**
     * Generates a time-appropriate greeting based on the current hour.
     */
    private fun generateGreeting(): String {
        val hour = LocalTime.now().hour
        return when {
            hour < 6 -> "Good night"
            hour < 12 -> "Good morning"
            hour < 17 -> "Good afternoon"
            hour < 21 -> "Good evening"
            else -> "Good night"
        }
    }
}
