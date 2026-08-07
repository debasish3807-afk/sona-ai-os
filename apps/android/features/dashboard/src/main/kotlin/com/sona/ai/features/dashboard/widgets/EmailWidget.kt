package com.sona.ai.features.dashboard.widgets

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Email
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/**
 * Widget showing email summary with unread count.
 */
@Composable
fun EmailWidget(
    summary: String,
    unreadCount: Int,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "Email ($unreadCount unread)",
        icon = Icons.Default.Email,
        modifier = modifier
    ) {
        Text(
            text = summary,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}
