package com.sona.ai.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.sona.ai.features.agents.AgentsScreen
import com.sona.ai.features.camera.CameraScreen
import com.sona.ai.features.chat.ChatScreen
import com.sona.ai.features.files.FilePickerScreen
import com.sona.ai.features.memory.MemoryScreen
import com.sona.ai.features.settings.SettingsScreen
import com.sona.ai.features.vision.VisionScreen
import com.sona.ai.features.voice.VoiceScreen
import com.sona.ai.ui.screens.HomeScreen
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
            HomeScreen(
                onNavigateToChat = {
                    navController.navigate(Screen.Chat.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onNavigateToMemory = {
                    navController.navigate(Screen.Memory.route)
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
    }
}
