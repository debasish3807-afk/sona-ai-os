package com.sona.ai.features.vision.document

import android.content.Context
import android.net.Uri
import com.sona.ai.features.vision.DocumentOutput
import com.sona.ai.features.vision.ocr.PdfOcrProcessor
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Processes documents of various formats (PDF, text, markdown).
 * Routes processing based on MIME type and extracts structured data.
 */
@Singleton
class DocumentProcessor @Inject constructor(
    @ApplicationContext private val context: Context,
    private val pdfOcr: PdfOcrProcessor
) {
    /**
     * Process a document and extract structured information.
     *
     * @param documentUri URI pointing to the document file
     * @return [DocumentOutput] with title, summary, extracted text, and tables
     */
    suspend fun process(documentUri: Uri): DocumentOutput {
        val mimeType = context.contentResolver.getType(documentUri) ?: "application/octet-stream"
        return when {
            mimeType.contains("pdf") -> processPdf(documentUri)
            mimeType.contains("text") || mimeType.contains("markdown") -> processText(documentUri)
            else -> DocumentOutput(
                title = "Unknown Document",
                summary = "Unsupported format: $mimeType"
            )
        }
    }

    /**
     * Process a PDF document using OCR.
     */
    private suspend fun processPdf(uri: Uri): DocumentOutput {
        val ocrResult = pdfOcr.extractFromPdf(uri)
        val summary = if (ocrResult.text.length > 200) {
            ocrResult.text.take(200) + "..."
        } else {
            ocrResult.text
        }
        return DocumentOutput(
            title = "PDF Document",
            summary = summary,
            extractedText = ocrResult.text,
            pages = ocrResult.text.split("\n\n").size
        )
    }

    /**
     * Process a plain text or markdown document.
     */
    private fun processText(uri: Uri): DocumentOutput {
        val text = context.contentResolver.openInputStream(uri)
            ?.bufferedReader()
            ?.readText() ?: ""
        val summary = if (text.length > 200) {
            text.take(200) + "..."
        } else {
            text
        }
        return DocumentOutput(
            title = "Text Document",
            summary = summary,
            extractedText = text
        )
    }
}
