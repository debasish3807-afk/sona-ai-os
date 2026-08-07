package com.sona.ai.features.dashboard.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.dashboard.ScheduleItem

/**
 * Widget showing today's scheduled meetings and events.
 */
@Composable
fun ScheduleWidget(
    items: List<ScheduleItem>,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "Today's Schedule",
        icon = Icons.Default.Schedule,
        modifier = modifier
    ) {
        items.forEach { item ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = item.time,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary
                )
                Column {
                    Text(
                        text = item.title,
                        style = MaterialTheme.typography.bodyMedium
                    )
                    if (item.location.isNotEmpty()) {
                        Text(
                            text = item.location,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }
        }
    }
}
