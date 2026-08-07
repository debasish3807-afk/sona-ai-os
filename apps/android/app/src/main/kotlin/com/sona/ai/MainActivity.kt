package com.sona.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.sona.ai.domain.model.AppTheme
import com.sona.ai.domain.repository.SettingsRepository
import com.sona.ai.navigation.SonaNavGraph
import com.sona.ai.ui.theme.SonaTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

/**
 * Main activity - single entry point for the compose-based app.
 * Uses Hilt for DI and Navigation Compose for screen routing.
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var settingsRepository: SettingsRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            val settings by settingsRepository.getSettings()
                .collectAsState(initial = com.sona.ai.domain.model.AppSettings())

            SonaTheme(appTheme = settings.theme) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val navController = rememberNavController()
                    SonaNavGraph(navController = navController)
                }
            }
        }
    }
}
