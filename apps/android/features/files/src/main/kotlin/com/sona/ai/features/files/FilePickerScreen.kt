package com.sona.ai.features.files

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.FilePresent
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

/**
 * File picker screen for selecting and uploading documents to AI.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilePickerScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: FilePickerViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val documentPicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri -> viewModel.onFileSelected(uri) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Files") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            when (val currentState = state) {
                is FilePickerState.Idle -> IdleContent(
                    onPickFile = {
                        documentPicker.launch(
                            arrayOf(
                                "text/plain",
                                "text/markdown",
                                "text/csv",
                                "application/json",
                                "application/pdf"
                            )
                        )
                    }
                )
                is FilePickerState.FileSelected -> FileSelectedContent(
                    fileName = currentState.fileName,
                    fileSize = currentState.fileSize,
                    mimeType = currentState.mimeType,
                    preview = currentState.preview,
                    onUpload = viewModel::uploadFile,
                    onCancel = viewModel::reset
                )
                is FilePickerState.Reading -> ReadingContent(
                    fileName = currentState.fileName,
                    progress = currentState.progress
                )
                is FilePickerState.Uploading -> UploadingContent(
                    fileName = currentState.fileName,
                    progress = currentState.progress
                )
                is FilePickerState.Complete -> CompleteContent(
                    fileName = currentState.fileName,
                    response = currentState.response,
                    onDone = viewModel::reset
                )
                is FilePickerState.Error -> ErrorContent(
                    message = currentState.message,
                    onRetry = viewModel::reset
                )
            }
        }
    }
}

@Composable
private fun IdleContent(onPickFile: () -> Unit) {
    Icon(
        Icons.Default.UploadFile,
        contentDescription = null,
        modifier = Modifier.padding(bottom = 16.dp),
        tint = MaterialTheme.colorScheme.primary
    )
    Text(
        text = "Send documents to AI",
        style = MaterialTheme.typography.headlineSmall
    )
    Spacer(Modifier.height(8.dp))
    Text(
        text = "Supports PDF, TXT, Markdown, CSV, and JSON",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
    Spacer(Modifier.height(24.dp))
    Button(onClick = onPickFile) {
        Icon(Icons.Default.FilePresent, contentDescription = null)
        Spacer(Modifier.width(8.dp))
        Text("Choose File")
    }
}

@Composable
private fun FileSelectedContent(
    fileName: String,
    fileSize: Long,
    mimeType: String,
    preview: String?,
    onUpload: () -> Unit,
    onCancel: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Description, contentDescription = null)
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = fileName,
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "${formatFileSize(fileSize)} • $mimeType",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            if (preview != null) {
                Spacer(Modifier.height(12.dp))
                Text(
                    text = preview,
                    style = MaterialTheme.typography.bodySmall,
                    maxLines = 6,
                    overflow = TextOverflow.Ellipsis,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }

    Spacer(Modifier.height(24.dp))

    Row(modifier = Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = onCancel, modifier = Modifier.weight(1f)) {
            Text("Cancel")
        }
        Spacer(Modifier.width(12.dp))
        Button(onClick = onUpload, modifier = Modifier.weight(1f)) {
            Icon(Icons.Default.Send, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("Send to AI")
        }
    }
}

@Composable
private fun ReadingContent(fileName: String, progress: Float) {
    CircularProgressIndicator()
    Spacer(Modifier.height(16.dp))
    Text(text = "Reading $fileName...")
}

@Composable
private fun UploadingContent(fileName: String, progress: Float) {
    Text(text = "Uploading $fileName...")
    Spacer(Modifier.height(16.dp))
    LinearProgressIndicator(
        progress = { progress },
        modifier = Modifier.fillMaxWidth()
    )
}

@Composable
private fun CompleteContent(fileName: String, response: String, onDone: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "AI Response for $fileName",
            style = MaterialTheme.typography.titleMedium
        )
        Spacer(Modifier.height(12.dp))
        Text(
            text = response,
            style = MaterialTheme.typography.bodyLarge
        )
        Spacer(Modifier.height(24.dp))
        Button(onClick = onDone, modifier = Modifier.fillMaxWidth()) {
            Text("Upload Another")
        }
    }
}

@Composable
private fun ErrorContent(message: String, onRetry: () -> Unit) {
    Text(
        text = message,
        style = MaterialTheme.typography.bodyLarge,
        color = MaterialTheme.colorScheme.error
    )
    Spacer(Modifier.height(16.dp))
    TextButton(onClick = onRetry) { Text("Try Again") }
}

private fun formatFileSize(bytes: Long): String = when {
    bytes < 1024 -> "$bytes B"
    bytes < 1024 * 1024 -> "${bytes / 1024} KB"
    else -> "${bytes / (1024 * 1024)} MB"
}
