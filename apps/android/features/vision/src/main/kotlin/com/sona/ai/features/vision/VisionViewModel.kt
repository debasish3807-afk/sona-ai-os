package com.sona.ai.features.vision

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.features.vision.analysis.VisionAnalyzer
import com.sona.ai.features.vision.document.DocumentProcessor
import com.sona.ai.features.vision.ocr.OcrEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Vision AI feature.
 * Orchestrates OCR, image analysis, and document processing operations.
 */
@HiltViewModel
class VisionViewModel @Inject constructor(
    private val ocrEngine: OcrEngine,
    private val analyzer: VisionAnalyzer,
    private val documentProcessor: DocumentProcessor
) : ViewModel() {

    private val _state = MutableStateFlow<VisionState>(VisionState.Idle)
    val state: StateFlow<VisionState> = _state.asStateFlow()

    /**
     * Process OCR text extraction on the given image.
     */
    fun processOcr(imageUri: Uri) {
        viewModelScope.launch {
            _state.value = VisionState.Processing
            try {
                val result = ocrEngine.extractText(imageUri)
                _state.value = VisionState.OcrResult(result)
            } catch (e: Exception) {
                _state.value = VisionState.Error(
                    e.message ?: "OCR processing failed"
                )
            }
        }
    }

    /**
     * Analyze an image using AI vision capabilities.
     */
    fun analyzeImage(imageUri: Uri) {
        viewModelScope.launch {
            _state.value = VisionState.Processing
            try {
                val result = analyzer.analyze(imageUri)
                _state.value = VisionState.AnalysisResult(result)
            } catch (e: Exception) {
                _state.value = VisionState.Error(
                    e.message ?: "Image analysis failed"
                )
            }
        }
    }

    /**
     * Process a document (PDF, text, markdown).
     */
    fun processDocument(documentUri: Uri) {
        viewModelScope.launch {
            _state.value = VisionState.Processing
            try {
                val result = documentProcessor.process(documentUri)
                _state.value = VisionState.DocumentResult(result)
            } catch (e: Exception) {
                _state.value = VisionState.Error(
                    e.message ?: "Document processing failed"
                )
            }
        }
    }

    /**
     * Reset the state back to idle.
     */
    fun reset() {
        _state.value = VisionState.Idle
    }
}
