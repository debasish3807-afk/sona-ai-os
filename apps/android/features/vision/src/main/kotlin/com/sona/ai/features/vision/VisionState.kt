package com.sona.ai.features.vision

/**
 * Sealed interface representing all possible states of the Vision AI feature.
 */
sealed interface VisionState {
    /** Initial idle state - no processing active. */
    data object Idle : VisionState

    /** Processing is in progress. */
    data object Processing : VisionState

    /** OCR text extraction completed successfully. */
    data class OcrResult(val result: OcrOutput) : VisionState

    /** Image analysis completed successfully. */
    data class AnalysisResult(val result: AnalysisOutput) : VisionState

    /** Document processing completed successfully. */
    data class DocumentResult(val result: DocumentOutput) : VisionState

    /** An error occurred during processing. */
    data class Error(val message: String) : VisionState
}

/**
 * Output from OCR text recognition.
 *
 * @param text The full extracted text content
 * @param confidence Overall confidence score (0.0 to 1.0)
 * @param language Detected language code
 * @param blocks Individual text blocks with position info
 */
data class OcrOutput(
    val text: String,
    val confidence: Float = 0f,
    val language: String = "",
    val blocks: List<TextBlock> = emptyList()
)

/**
 * A single block of recognized text with spatial information.
 *
 * @param text The text content of this block
 * @param boundingBox String representation of the bounding rectangle
 * @param confidence Confidence score for this block (0.0 to 1.0)
 */
data class TextBlock(
    val text: String,
    val boundingBox: String = "",
    val confidence: Float = 0f
)

/**
 * Output from image analysis.
 *
 * @param description Natural language description of the image
 * @param labels Detected labels/tags
 * @param category Classification category (e.g., "screenshot", "diagram")
 * @param suggestions AI-generated suggestions based on the image content
 */
data class AnalysisOutput(
    val description: String,
    val labels: List<String> = emptyList(),
    val category: String = "",
    val suggestions: List<String> = emptyList()
)

/**
 * Output from document processing.
 *
 * @param title Detected or assigned document title
 * @param summary Auto-generated summary of the document
 * @param pages Number of pages processed
 * @param tables Extracted table data
 * @param extractedText Full extracted text content
 */
data class DocumentOutput(
    val title: String = "",
    val summary: String = "",
    val pages: Int = 0,
    val tables: List<TableData> = emptyList(),
    val extractedText: String = ""
)

/**
 * Represents a parsed table structure.
 *
 * @param headers Column header names
 * @param rows Table data rows (each row is a list of cell values)
 */
data class TableData(
    val headers: List<String>,
    val rows: List<List<String>>
)
