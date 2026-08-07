package com.sona.ai.features.dashboard.widgets

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Code
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/**
 * Widget showing GitHub activity summary (PRs, issues, CI status).
 */
@Composable
fun GitHubWidget(
    summary: String,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "GitHub",
        icon = Icons.Default.Code,
        modifier = modifier
    ) {
        Text(
            text = summary,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}
