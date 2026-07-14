package com.sona.ai.ui.navigation

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sona.ai.ui.screens.*

sealed class Screen(val route: String, val title: String) {
    data object Chat : Screen("chat", "AI Chat")
    data object Voice : Screen("voice", "Voice")
    data object Vision : Screen("vision", "Vision")
    data object Research : Screen("research", "Research")
    data object Memory : Screen("memory", "Memory")
    data object Files : Screen("files", "Files")
    data object Settings : Screen("settings", "Settings")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SonaNavHost() {
    val navController = rememberNavController()
    var selectedRoute by remember { mutableStateOf("chat") }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    icon = { Icon(Icons.Default.Chat, "Chat") },
                    label = { Text("Chat") },
                    selected = selectedRoute == "chat",
                    onClick = { selectedRoute = "chat"; navController.navigate("chat") }
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Default.Mic, "Voice") },
                    label = { Text("Voice") },
                    selected = selectedRoute == "voice",
                    onClick = { selectedRoute = "voice"; navController.navigate("voice") }
                )
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = "chat",
            modifier = Modifier.padding(padding)
        ) {
            composable("chat") { ChatScreen() }
            composable("voice") { VoiceScreen() }
            composable("vision") { VisionScreen() }
            composable("research") { ResearchScreen() }
            composable("memory") { MemoryScreen() }
            composable("files") { FilesScreen() }
            composable("settings") { SettingsScreen() }
        }
    }
}
