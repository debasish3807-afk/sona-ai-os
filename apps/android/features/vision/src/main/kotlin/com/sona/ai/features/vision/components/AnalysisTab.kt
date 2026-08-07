package com.sona.ai.features.vision.components

import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AssistChip
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sona.ai.features.vision.VisionState

/**
 * Analysis tab content - allows users to analyze images using AI.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AnalysisTab(
    state: VisionState,
    onAnalyze: (Uri) -> Unit,
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
            text = "Image Analysis",
            style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Select an image to get AI-powered analysis with labels, descriptions, and suggestions.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        ImagePicker(
            onImageSelected = onAnalyze,
            label = "Select Image for Analysis"
        )

        Spacer(modifier = Modifier.height(24.dp))

        when (state) {
            is VisionState.Processing -> {
                CircularProgressIndicator()
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Analyzing image...",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            is VisionState.AnalysisResult -> {
                ResultCard(
                    title = "Analysis Result",
                    subtitle = "Category: ${state.result.category}",
                    content = state.result.description,
                    onDismiss = onReset
                )

                if (state.result.labels.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Labels",
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        state.result.labels.forEach { label ->
                            AssistChip(
                                onClick = { },
                                label = { Text(label) }
                            )
                        }
                    }
                }

                if (state.result.suggestions.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Suggestions",
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.fillMaxWidth()
                    )
                    state.result.suggestions.forEach { suggestion ->
                        Text(
                            text = "\u2022 $suggestion",
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(start = 8.dp, top = 4.dp)
                        )
                    }
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
