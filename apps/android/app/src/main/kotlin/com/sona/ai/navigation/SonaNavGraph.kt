package com.sona.ai.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.sona.ai.features.agents.AgentsScreen
import com.sona.ai.features.beta.DiagnosticsScreen
import com.sona.ai.features.beta.FeedbackScreen
import com.sona.ai.features.camera.CameraScreen
import com.sona.ai.features.chat.ChatScreen
import com.sona.ai.features.communication.CommunicationScreen
import com.sona.ai.features.connectors.ConnectorsScreen
import com.sona.ai.features.dashboard.DashboardScreen
import com.sona.ai.features.files.FilePickerScreen
import com.sona.ai.features.memory.MemoryScreen
import com.sona.ai.features.settings.SettingsScreen
import com.sona.ai.features.vision.VisionScreen
import com.sona.ai.features.voice.VoiceScreen
import com.sona.ai.ui.screens.LoginScreen
import com.sona.ai.ui.screens.SplashScreen

/**
 * Main navigation graph for the Sona AI app.
 * Defines all routes and their corresponding composable screens.
 */
@Composable
fun SonaNavGraph(
    navController: NavHostController,
    modifier: Modifier = Modifier,
    startDestination: String = Screen.Splash.route
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier
    ) {
        composable(Screen.Splash.route) {
            SplashScreen(
                onNavigateToLogin = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Splash.route) { inclusive = true }
                    }
                },
                onNavigateToHome = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Splash.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Home.route) {
            DashboardScreen(
                onNavigateToChat = {
                    navController.navigate(Screen.Chat.route)
                },
                onNavigateToVoice = {
                    navController.navigate(Screen.Voice.route)
                },
                onNavigateToCamera = {
                    navController.navigate(Screen.Camera.route)
                },
                onNavigateToVision = {
                    navController.navigate(Screen.Vision.route)
                },
                onNavigateToFiles = {
                    navController.navigate(Screen.Files.route)
                },
                onNavigateToMemory = {
                    navController.navigate(Screen.Memory.route)
                },
                onNavigateToAgents = {
                    navController.navigate(Screen.Agents.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onNavigateToConnectors = {
                    navController.navigate(Screen.Connectors.route)
                },
                onNavigateToCommunication = {
                    navController.navigate(Screen.Communication.route)
                }
            )
        }

        composable(Screen.Chat.route) {
            ChatScreen()
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Memory.route) {
            MemoryScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Voice.route) {
            VoiceScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Camera.route) {
            CameraScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Files.route) {
            FilePickerScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Agents.route) {
            AgentsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Vision.route) {
            VisionScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Communication.route) {
            CommunicationScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Connectors.route) {
            ConnectorsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Feedback.route) {
            FeedbackScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Diagnostics.route) {
            DiagnosticsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
