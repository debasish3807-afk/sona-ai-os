package com.sona.ai.features.dashboard.widgets

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.sona.ai.features.dashboard.ConversationPreview

/**
 * Widget showing recent AI conversation previews.
 */
@Composable
fun ConversationsWidget(
    conversations: List<ConversationPreview>,
    modifier: Modifier = Modifier
) {
    DashboardCard(
        title = "Recent Conversations",
        icon = Icons.Default.Forum,
        modifier = modifier
    ) {
        conversations.forEach { conv ->
            Column(modifier = Modifier.padding(vertical = 4.dp)) {
                Text(
                    text = conv.title,
                    style = MaterialTheme.typography.bodyMedium
                )
                Text(
                    text = "${conv.lastMessage} \u2022 ${conv.timeAgo}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.outline,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}
