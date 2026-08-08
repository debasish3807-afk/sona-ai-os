package com.sona.ai.features.beta

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedbackScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: FeedbackViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    var feedbackType by remember { mutableStateOf("bug") }
    var description by remember { mutableStateOf("") }
    var includeDeviceInfo by remember { mutableStateOf(true) }
    var includeLogs by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Send Feedback") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
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
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Feedback type selector
            Text("What kind of feedback?", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = feedbackType == "bug",
                    onClick = { feedbackType = "bug" },
                    label = { Text("Bug Report") },
                    leadingIcon = {
                        Icon(Icons.Default.BugReport, "Bug", modifier = Modifier.size(18.dp))
                    }
                )
                FilterChip(
                    selected = feedbackType == "feature",
                    onClick = { feedbackType = "feature" },
                    label = { Text("Feature Request") },
                    leadingIcon = {
                        Icon(Icons.Default.Lightbulb, "Feature", modifier = Modifier.size(18.dp))
                    }
                )
                FilterChip(
                    selected = feedbackType == "other",
                    onClick = { feedbackType = "other" },
                    label = { Text("Other") }
                )
            }

            // Description
            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Describe your feedback") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp),
                maxLines = 10
            )

            // Options
            Row {
                Checkbox(checked = includeDeviceInfo, onCheckedChange = { includeDeviceInfo = it })
                Text("Include device info", modifier = Modifier.padding(start = 8.dp))
            }
            Row {
                Checkbox(checked = includeLogs, onCheckedChange = { includeLogs = it })
                Text("Include recent logs", modifier = Modifier.padding(start = 8.dp))
            }

            // Submit
            Button(
                onClick = {
                    viewModel.submit(feedbackType, description, includeDeviceInfo, includeLogs)
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = description.isNotBlank()
            ) {
                Text("Submit Feedback")
            }

            if (state.submitted) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Text(
                        "Thank you for your feedback!",
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
        }
    }
}
