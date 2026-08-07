package com.sona.ai.features.files

import android.net.Uri

/**
 * UI state for the file picker screen.
 */
sealed interface FilePickerState {

    /** Ready to pick a file. */
    data object Idle : FilePickerState

    /** A file has been selected and is being previewed. */
    data class FileSelected(
        val fileUri: Uri,
        val fileName: String,
        val fileSize: Long,
        val mimeType: String,
        val preview: String? = null
    ) : FilePickerState

    /** File content is being read/parsed. */
    data class Reading(
        val fileName: String,
        val progress: Float = 0f
    ) : FilePickerState

    /** File is being uploaded to the AI gateway. */
    data class Uploading(
        val fileName: String,
        val progress: Float = 0f
    ) : FilePickerState

    /** Upload complete. */
    data class Complete(
        val fileName: String,
        val response: String
    ) : FilePickerState

    /** An error occurred. */
    data class Error(
        val message: String
    ) : FilePickerState
}

/**
 * Supported document types for reading.
 */
enum class DocumentType(val mimeTypes: List<String>, val extension: String) {
    PDF(listOf("application/pdf"), "pdf"),
    MARKDOWN(listOf("text/markdown", "text/x-markdown"), "md"),
    PLAIN_TEXT(listOf("text/plain"), "txt"),
    CSV(listOf("text/csv"), "csv"),
    JSON(listOf("application/json"), "json"),
    UNKNOWN(emptyList(), "")
}

/**
 * One-time UI events for the file picker.
 */
sealed interface FilePickerEvent {
    data class ShowError(val message: String) : FilePickerEvent
    data object FileUploaded : FilePickerEvent
    data object StoragePermissionRequired : FilePickerEvent
}
