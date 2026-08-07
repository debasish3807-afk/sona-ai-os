package com.sona.ai.features.dashboard.widgets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.ElevatedFilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

/**
 * Data class representing a quick action button.
 */
private data class QuickAction(
    val label: String,
    val icon: ImageVector,
    val onClick: () -> Unit
)

/**
 * Horizontal scrollable row of quick action chips for rapid navigation.
 */
@Composable
fun QuickActionsRow(
    onChat: () -> Unit,
    onVoice: () -> Unit,
    onCamera: () -> Unit,
    onVision: () -> Unit,
    onFiles: () -> Unit,
    onMemory: () -> Unit,
    onAgents: () -> Unit,
    modifier: Modifier = Modifier
) {
    val actions = listOf(
        QuickAction("Chat", Icons.Default.Chat, onChat),
        QuickAction("Voice", Icons.Default.Mic, onVoice),
        QuickAction("Camera", Icons.Default.CameraAlt, onCamera),
        QuickAction("Vision", Icons.Default.Visibility, onVision),
        QuickAction("Files", Icons.Default.Folder, onFiles),
        QuickAction("Memory", Icons.Default.Psychology, onMemory),
        QuickAction("Agents", Icons.Default.SmartToy, onAgents)
    )

    LazyRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(actions) { action ->
            QuickActionChip(
                label = action.label,
                icon = action.icon,
                onClick = action.onClick
            )
        }
    }
}

@Composable
private fun QuickActionChip(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit
) {
    ElevatedFilterChip(
        selected = false,
        onClick = onClick,
        label = { Text(label) },
        leadingIcon = {
            Icon(
                imageVector = icon,
                contentDescription = label,
                modifier = Modifier.size(18.dp)
            )
        }
    )
}
