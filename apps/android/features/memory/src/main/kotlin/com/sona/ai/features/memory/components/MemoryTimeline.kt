package com.sona.ai.features.memory.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.memory.MemoryItem
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/**
 * Chronological timeline view for memories.
 * Groups memories by date for easy browsing.
 */
@Composable
fun MemoryTimeline(
    memories: List<MemoryItem>,
    onDeleteMemory: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    if (memories.isEmpty()) {
        EmptyMemoryState(modifier = modifier)
        return
    }

    val groupedMemories = memories
        .sortedByDescending { it.timestamp }
        .groupBy { getDateLabel(it.timestamp) }

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        groupedMemories.forEach { (dateLabel, memoriesInGroup) ->
            item {
                Text(
                    text = dateLabel,
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }

            items(
                items = memoriesInGroup,
                key = { it.id }
            ) { memory ->
                MemoryCard(
                    memory = memory,
                    onDelete = { onDeleteMemory(memory.id) },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

@Composable
private fun EmptyMemoryState(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "No memories yet",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = "Sona will remember important things from your conversations",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 8.dp)
        )
    }
}

private fun getDateLabel(timestamp: Long): String {
    val calendar = Calendar.getInstance()
    val today = Calendar.getInstance()

    calendar.timeInMillis = timestamp

    return when {
        isSameDay(calendar, today) -> "Today"
        isSameDay(calendar, today.apply { add(Calendar.DAY_OF_YEAR, -1) }) -> "Yesterday"
        isThisWeek(calendar) -> {
            SimpleDateFormat("EEEE", Locale.getDefault()).format(Date(timestamp))
        }
        else -> {
            SimpleDateFormat("MMMM d, yyyy", Locale.getDefault()).format(Date(timestamp))
        }
    }
}

private fun isSameDay(cal1: Calendar, cal2: Calendar): Boolean {
    return cal1.get(Calendar.YEAR) == cal2.get(Calendar.YEAR) &&
            cal1.get(Calendar.DAY_OF_YEAR) == cal2.get(Calendar.DAY_OF_YEAR)
}

private fun isThisWeek(calendar: Calendar): Boolean {
    val now = Calendar.getInstance()
    return calendar.get(Calendar.YEAR) == now.get(Calendar.YEAR) &&
            calendar.get(Calendar.WEEK_OF_YEAR) == now.get(Calendar.WEEK_OF_YEAR)
}
