package com.sona.ai.features.dashboard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.sona.ai.features.dashboard.widgets.ConversationsWidget
import com.sona.ai.features.dashboard.widgets.ContinueWorkingWidget
import com.sona.ai.features.dashboard.widgets.EmailWidget
import com.sona.ai.features.dashboard.widgets.GitHubWidget
import com.sona.ai.features.dashboard.widgets.GreetingWidget
import com.sona.ai.features.dashboard.widgets.MemoryWidget
import com.sona.ai.features.dashboard.widgets.QuickActionsRow
import com.sona.ai.features.dashboard.widgets.ScheduleWidget
import com.sona.ai.features.dashboard.widgets.TasksWidget

/**
 * Main AI-powered Dashboard screen.
 * Replaces the basic HomeScreen with a rich daily driver dashboard
 * showing schedule, tasks, GitHub, email, memory highlights, and more.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    onNavigateToChat: () -> Unit = {},
    onNavigateToVoice: () -> Unit = {},
    onNavigateToCamera: () -> Unit = {},
    onNavigateToVision: () -> Unit = {},
    onNavigateToFiles: () -> Unit = {},
    onNavigateToMemory: () -> Unit = {},
    onNavigateToAgents: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {},
    onNavigateToConnectors: () -> Unit = {},
    onNavigateToCommunication: () -> Unit = {},
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Sona AI",
                        fontWeight = FontWeight.Bold
                    )
                },
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        }
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            // Loading indicator
            AnimatedVisibility(
                visible = state.isLoading,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator()
                        Spacer(Modifier.height(16.dp))
                        Text(
                            text = "Loading your dashboard...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }

            // Refreshing indicator
            if (state.isRefreshing) {
                LinearProgressIndicator(
                    modifier = Modifier.fillMaxWidth().align(Alignment.TopCenter)
                )
            }

            // Main dashboard content
            AnimatedVisibility(
                visible = !state.isLoading,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Greeting & Daily Brief
                    item {
                        GreetingWidget(
                            greeting = state.greeting,
                            briefing = state.dailyBrief
                        )
                    }

                    // Quick Actions Row
                    item {
                        QuickActionsRow(
                            onChat = onNavigateToChat,
                            onVoice = onNavigateToVoice,
                            onCamera = onNavigateToCamera,
                            onVision = onNavigateToVision,
                            onFiles = onNavigateToFiles,
                            onMemory = onNavigateToMemory,
                            onAgents = onNavigateToAgents
                        )
                    }

                    // Today's Schedule
                    if (state.scheduleItems.isNotEmpty()) {
                        item {
                            ScheduleWidget(items = state.scheduleItems)
                        }
                    }

                    // GitHub Summary
                    if (state.githubSummary.isNotEmpty()) {
                        item {
                            GitHubWidget(summary = state.githubSummary)
                        }
                    }

                    // Email Summary
                    if (state.emailSummary.isNotEmpty()) {
                        item {
                            EmailWidget(
                                summary = state.emailSummary,
                                unreadCount = state.unreadEmails
                            )
                        }
                    }

                    // Tasks
                    if (state.tasks.isNotEmpty()) {
                        item {
                            TasksWidget(tasks = state.tasks)
                        }
                    }

                    // Memory Highlights
                    if (state.memoryHighlights.isNotEmpty()) {
                        item {
                            MemoryWidget(highlights = state.memoryHighlights)
                        }
                    }

                    // Recent Conversations
                    if (state.recentConversations.isNotEmpty()) {
                        item {
                            ConversationsWidget(conversations = state.recentConversations)
                        }
                    }

                    // Continue Working
                    if (state.continueWorking.isNotEmpty()) {
                        item {
                            ContinueWorkingWidget(items = state.continueWorking)
                        }
                    }

                    // Bottom spacer for FAB clearance
                    item { Spacer(Modifier.height(80.dp)) }
                }
            }
        }
    }
}
