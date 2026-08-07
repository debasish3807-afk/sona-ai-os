package com.sona.ai.features.voice

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

/**
 * Voice chat screen that manages STT → AI → TTS interactions.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: VoiceViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Voice Chat") },
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
                .padding(padding),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            when (val currentState = state) {
                is VoiceState.Idle -> IdleContent(onStartListening = viewModel::startListening)
                is VoiceState.Listening -> ListeningContent(
                    amplitude = currentState.amplitude,
                    onStop = viewModel::stopListening
                )
                is VoiceState.Processing -> ProcessingContent(
                    transcribedText = currentState.transcribedText
                )
                is VoiceState.Speaking -> SpeakingContent(
                    text = currentState.text,
                    onStop = viewModel::stopSpeaking
                )
                is VoiceState.Error -> ErrorContent(
                    message = currentState.message,
                    onRetry = viewModel::startListening
                )
            }
        }
    }
}

@Composable
private fun IdleContent(onStartListening: () -> Unit) {
    Text(
        text = "Tap to speak",
        style = MaterialTheme.typography.headlineMedium,
        color = MaterialTheme.colorScheme.onSurface
    )
    Spacer(Modifier.height(24.dp))
    FloatingActionButton(
        onClick = onStartListening,
        modifier = Modifier.size(72.dp),
        containerColor = MaterialTheme.colorScheme.primary
    ) {
        Icon(
            Icons.Default.Mic,
            contentDescription = "Start listening",
            modifier = Modifier.size(32.dp)
        )
    }
}

@Composable
private fun ListeningContent(amplitude: Float, onStop: () -> Unit) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(600),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Text(
        text = "Listening...",
        style = MaterialTheme.typography.headlineMedium,
        color = MaterialTheme.colorScheme.primary
    )
    Spacer(Modifier.height(24.dp))
    FloatingActionButton(
        onClick = onStop,
        modifier = Modifier
            .size(72.dp)
            .scale(scale),
        containerColor = MaterialTheme.colorScheme.error
    ) {
        Icon(
            Icons.Default.MicOff,
            contentDescription = "Stop listening",
            modifier = Modifier.size(32.dp)
        )
    }
}

@Composable
private fun ProcessingContent(transcribedText: String) {
    if (transcribedText.isNotEmpty()) {
        Text(
            text = "\"$transcribedText\"",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 32.dp)
        )
        Spacer(Modifier.height(16.dp))
    }
    CircularProgressIndicator()
    Spacer(Modifier.height(8.dp))
    Text(
        text = "Processing...",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

@Composable
private fun SpeakingContent(text: String, onStop: () -> Unit) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyLarge,
        textAlign = TextAlign.Center,
        modifier = Modifier.padding(horizontal = 32.dp)
    )
    Spacer(Modifier.height(24.dp))
    FloatingActionButton(
        onClick = onStop,
        modifier = Modifier.size(56.dp),
        containerColor = MaterialTheme.colorScheme.secondary
    ) {
        Icon(Icons.Default.Stop, contentDescription = "Stop speaking")
    }
}

@Composable
private fun ErrorContent(message: String, onRetry: () -> Unit) {
    Text(
        text = message,
        style = MaterialTheme.typography.bodyLarge,
        color = MaterialTheme.colorScheme.error,
        textAlign = TextAlign.Center,
        modifier = Modifier.padding(horizontal = 32.dp)
    )
    Spacer(Modifier.height(16.dp))
    TextButton(onClick = onRetry) {
        Text("Try Again")
    }
}
