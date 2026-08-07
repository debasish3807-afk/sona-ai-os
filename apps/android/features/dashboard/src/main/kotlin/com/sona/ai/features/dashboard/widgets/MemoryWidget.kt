package com.sona.ai.features.dashboard.widgets

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.dashboard.MemoryHighlight

/**
 * Widget showing recent memory highlights from Sona's memory system.
 */
@Composable
fun MemoryWidget(
    highlights: List<MemoryHighlight>,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "Memory Highlights",
        icon = Icons.Default.Psychology,
        modifier = modifier
    ) {
        highlights.forEach { item ->
            Column(modifier = Modifier.padding(vertical = 4.dp)) {
                Text(
                    text = item.content,
                    style = MaterialTheme.typography.bodyMedium
                )
                Text(
                    text = "${item.type} \u2022 ${item.timeAgo}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
    }
}
