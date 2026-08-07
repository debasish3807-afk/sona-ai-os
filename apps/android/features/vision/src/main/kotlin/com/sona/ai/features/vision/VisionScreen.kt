package com.sona.ai.features.vision

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import com.sona.ai.features.vision.components.AnalysisTab
import com.sona.ai.features.vision.components.DocumentsTab
import com.sona.ai.features.vision.components.OcrTab

/**
 * Main Vision AI screen with tabbed navigation for OCR, Analysis, and Documents.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VisionScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: VisionViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("OCR", "Analysis", "Documents")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Vision AI") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Navigate back"
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            TabRow(selectedTabIndex = selectedTab) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        text = { Text(title) }
                    )
                }
            }

            when (selectedTab) {
                0 -> OcrTab(state = state, onProcessOcr = viewModel::processOcr, onReset = viewModel::reset)
                1 -> AnalysisTab(state = state, onAnalyze = viewModel::analyzeImage, onReset = viewModel::reset)
                2 -> DocumentsTab(state = state, onProcess = viewModel::processDocument, onReset = viewModel::reset)
            }
        }
    }
}
