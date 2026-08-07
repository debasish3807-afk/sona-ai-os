package com.sona.ai.features.vision.components

import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.vision.VisionState

/**
 * Documents tab content - allows users to process PDF and text documents.
 */
@Composable
fun DocumentsTab(
    state: VisionState,
    onProcess: (Uri) -> Unit,
    onReset: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top
    ) {
        Text(
            text = "Document Processing",
            style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Select a document (PDF or text) to extract content, tables, and generate summaries.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        ImagePicker(
            onImageSelected = onProcess,
            label = "Select Document",
            mimeTypes = arrayOf("application/pdf", "text/*")
        )

        Spacer(modifier = Modifier.height(24.dp))

        when (state) {
            is VisionState.Processing -> {
                CircularProgressIndicator()
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Processing document...",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            is VisionState.DocumentResult -> {
                ResultCard(
                    title = state.result.title,
                    subtitle = if (state.result.pages > 0) "${state.result.pages} pages" else null,
                    content = state.result.summary,
                    onDismiss = onReset
                )

                if (state.result.extractedText.isNotEmpty() &&
                    state.result.extractedText != state.result.summary
                ) {
                    Spacer(modifier = Modifier.height(12.dp))
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Full Text",
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = state.result.extractedText,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                if (state.result.tables.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(12.dp))
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Tables Found: ${state.result.tables.size}",
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            is VisionState.Error -> {
                ResultCard(
                    title = "Error",
                    content = state.message,
                    isError = true,
                    onDismiss = onReset
                )
            }
            else -> { /* Idle */ }
        }
    }
}
