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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.vision.VisionState

/**
 * OCR tab content - allows users to select an image and extract text.
 */
@Composable
fun OcrTab(
    state: VisionState,
    onProcessOcr: (Uri) -> Unit,
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
            text = "Text Recognition (OCR)",
            style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Select an image to extract text using ML Kit on-device recognition.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        ImagePicker(
            onImageSelected = onProcessOcr,
            label = "Select Image for OCR"
        )

        Spacer(modifier = Modifier.height(24.dp))

        when (state) {
            is VisionState.Processing -> {
                CircularProgressIndicator()
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Extracting text...",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            is VisionState.OcrResult -> {
                ResultCard(
                    title = "Extracted Text",
                    subtitle = "Confidence: ${String.format("%.0f%%", state.result.confidence * 100)}",
                    content = state.result.text,
                    onDismiss = onReset
                )
                if (state.result.blocks.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Text Blocks: ${state.result.blocks.size}",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
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
            else -> { /* Idle - show nothing extra */ }
        }
    }
}
