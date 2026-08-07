package com.sona.ai.features.dashboard.widgets

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.dashboard.ContinueWorkingItem

/**
 * Widget showing items the user can resume working on.
 */
@Composable
fun ContinueWorkingWidget(
    items: List<ContinueWorkingItem>,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "Continue Working",
        icon = Icons.Default.PlayArrow,
        modifier = modifier
    ) {
        items.forEach { item ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = item.title,
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = item.context,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.outline
                    )
                }
            }
        }
    }
}
