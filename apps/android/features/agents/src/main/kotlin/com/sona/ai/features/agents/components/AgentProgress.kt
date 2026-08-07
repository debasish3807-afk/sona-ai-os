package com.sona.ai.features.agents.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.HourglassTop
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.agents.AgentExecution
import com.sona.ai.features.agents.AgentStep
import com.sona.ai.features.agents.ExecutionStatus

/**
 * Displays the progress of a running agent execution.
 */
@Composable
fun AgentProgress(
    execution: AgentExecution,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        // Header
        Text(
            text = "Running: ${execution.agentName}",
            style = MaterialTheme.typography.headlineSmall
        )
        Spacer(Modifier.height(8.dp))

        // Progress bar
        LinearProgressIndicator(
            progress = { execution.progress },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = "${(execution.progress * 100).toInt()}% complete",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(Modifier.height(16.dp))

        // Steps
        Text(
            text = "Steps",
            style = MaterialTheme.typography.titleMedium
        )
        Spacer(Modifier.height(8.dp))

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(execution.steps) { step ->
                StepItem(step = step)
            }
        }

        // Cancel button
        OutlinedButton(
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Default.Cancel, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("Cancel Execution")
        }
    }
}

@Composable
private fun StepItem(step: AgentStep) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = when (step.status) {
                ExecutionStatus.COMPLETED -> Icons.Default.CheckCircle
                ExecutionStatus.RUNNING -> Icons.Default.PlayCircle
                ExecutionStatus.QUEUED -> Icons.Default.HourglassTop
                else -> Icons.Default.Cancel
            },
            contentDescription = null,
            modifier = Modifier.size(20.dp),
            tint = when (step.status) {
                ExecutionStatus.COMPLETED -> MaterialTheme.colorScheme.primary
                ExecutionStatus.RUNNING -> MaterialTheme.colorScheme.tertiary
                ExecutionStatus.FAILED -> MaterialTheme.colorScheme.error
                else -> MaterialTheme.colorScheme.onSurfaceVariant
            }
        )
        Spacer(Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = step.description,
                style = MaterialTheme.typography.bodyMedium
            )
            step.output?.let { output ->
                Text(
                    text = output,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
