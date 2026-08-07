package com.sona.ai.features.communication

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CommunicationScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: CommunicationViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Communication AI") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                SectionCard(
                    title = "Notifications",
                    subtitle = "${state.unreadCount} unread",
                    icon = Icons.Default.Notifications,
                    onClick = { viewModel.summarizeNotifications() }
                )
            }
            item {
                SectionCard(
                    title = "Messages",
                    subtitle = "${state.messageCount} conversations",
                    icon = Icons.Default.Chat,
                    onClick = { viewModel.summarizeMessages() }
                )
            }
            item {
                SectionCard(
                    title = "Calls",
                    subtitle = "${state.missedCalls} missed",
                    icon = Icons.Default.Phone,
                    onClick = { viewModel.summarizeCalls() }
                )
            }
            item {
                SectionCard(
                    title = "Email",
                    subtitle = "${state.unreadEmails} unread",
                    icon = Icons.Default.Email,
                    onClick = { viewModel.summarizeEmails() }
                )
            }
            item {
                SectionCard(
                    title = "Contacts",
                    subtitle = "${state.contactInsights} insights",
                    icon = Icons.Default.People,
                    onClick = { viewModel.showContactInsights() }
                )
            }
            // Show AI summary if available
            if (state.summary.isNotEmpty()) {
                item { AISummaryCard(state.summary) }
            }
        }
    }
}

@Composable
private fun SectionCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    onClick: () -> Unit
) {
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Icon(icon, title, tint = MaterialTheme.colorScheme.primary)
            Column {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun AISummaryCard(summary: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.tertiaryContainer
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("AI Summary", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))
            Text(summary, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
