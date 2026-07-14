package com.sona.ai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun VoiceScreen() {
    CenteredContent("Voice Assistant", "Tap to speak")
}

@Composable
fun VisionScreen() {
    CenteredContent("Vision & OCR", "Capture or upload image")
}

@Composable
fun ResearchScreen() {
    CenteredContent("Deep Research", "Enter research topic")
}

@Composable
fun MemoryScreen() {
    CenteredContent("Memory", "Search and manage memory")
}

@Composable
fun FilesScreen() {
    CenteredContent("Files", "Browse workspace files")
}

@Composable
fun SettingsScreen() {
    CenteredContent("Settings", "Configure Sona AI")
}

@Composable
private fun CenteredContent(title: String, subtitle: String) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(title, style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(8.dp))
        Text(subtitle, style = MaterialTheme.typography.bodyLarge)
    }
}
