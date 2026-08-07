package com.sona.ai.features.files

import android.content.Context
import android.net.Uri
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.BufferedReader
import java.io.InputStreamReader
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Reads content from various document types (PDF, MD, TXT, CSV, JSON).
 * Extracts text content for sending to the AI.
 */
@Singleton
class DocumentReader @Inject constructor(
    @ApplicationContext private val context: Context
) {

    /**
     * Reads the text content from a document URI.
     * Returns the extracted text or null if the format is unsupported.
     */
    suspend fun readDocument(uri: Uri, mimeType: String): DocumentContent {
        val type = resolveDocumentType(mimeType)
        return when (type) {
            DocumentType.PLAIN_TEXT,
            DocumentType.MARKDOWN,
            DocumentType.CSV,
            DocumentType.JSON -> readTextFile(uri)
            DocumentType.PDF -> readPdfFile(uri)
            DocumentType.UNKNOWN -> DocumentContent(
                text = null,
                error = "Unsupported file format: $mimeType"
            )
        }
    }

    /**
     * Gets metadata for a file URI.
     */
    fun getFileMetadata(uri: Uri): FileMetadata {
        val cursor = context.contentResolver.query(uri, null, null, null, null)
        var name = "unknown"
        var size = 0L

        cursor?.use {
            if (it.moveToFirst()) {
                val nameIndex = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                val sizeIndex = it.getColumnIndex(android.provider.OpenableColumns.SIZE)
                if (nameIndex >= 0) name = it.getString(nameIndex) ?: "unknown"
                if (sizeIndex >= 0) size = it.getLong(sizeIndex)
            }
        }

        val mimeType = context.contentResolver.getType(uri) ?: "application/octet-stream"

        return FileMetadata(
            name = name,
            size = size,
            mimeType = mimeType,
            documentType = resolveDocumentType(mimeType)
        )
    }

    private fun readTextFile(uri: Uri): DocumentContent {
        return try {
            val text = context.contentResolver.openInputStream(uri)?.use { stream ->
                BufferedReader(InputStreamReader(stream)).readText()
            }
            DocumentContent(text = text)
        } catch (e: Exception) {
            DocumentContent(text = null, error = "Failed to read file: ${e.message}")
        }
    }

    private fun readPdfFile(uri: Uri): DocumentContent {
        // PDF reading requires PdfRenderer for basic text extraction
        return try {
            context.contentResolver.openFileDescriptor(uri, "r")?.use { pfd ->
                val renderer = android.graphics.pdf.PdfRenderer(pfd)
                val pageCount = renderer.pageCount
                val builder = StringBuilder()
                builder.append("[PDF Document - $pageCount page(s)]\n\n")
                // Note: PdfRenderer renders pages as bitmaps. 
                // For text extraction, a library like Apache PDFBox would be needed.
                // Here we provide metadata about the PDF.
                builder.append("Pages: $pageCount\n")
                renderer.close()
                DocumentContent(text = builder.toString())
            } ?: DocumentContent(text = null, error = "Cannot open PDF file")
        } catch (e: Exception) {
            DocumentContent(text = null, error = "Failed to read PDF: ${e.message}")
        }
    }

    private fun resolveDocumentType(mimeType: String): DocumentType {
        return DocumentType.entries.firstOrNull { type ->
            type.mimeTypes.any { it.equals(mimeType, ignoreCase = true) }
        } ?: DocumentType.UNKNOWN
    }
}

/**
 * Result of reading a document.
 */
data class DocumentContent(
    val text: String?,
    val error: String? = null
)

/**
 * Metadata about a file.
 */
data class FileMetadata(
    val name: String,
    val size: Long,
    val mimeType: String,
    val documentType: DocumentType
)
