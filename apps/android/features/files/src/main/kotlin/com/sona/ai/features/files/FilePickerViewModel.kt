package com.sona.ai.features.files

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the file picker feature.
 * Manages file selection → reading → upload flow.
 */
@HiltViewModel
class FilePickerViewModel @Inject constructor(
    private val documentReader: DocumentReader,
    private val fileUploadManager: FileUploadManager
) : ViewModel() {

    private val _state = MutableStateFlow<FilePickerState>(FilePickerState.Idle)
    val state: StateFlow<FilePickerState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<FilePickerEvent>()
    val events: SharedFlow<FilePickerEvent> = _events.asSharedFlow()

    private var currentFileUri: Uri? = null
    private var currentFileContent: String? = null

    /**
     * Called when a file is selected from the document picker.
     */
    fun onFileSelected(uri: Uri?) {
        if (uri == null) return

        currentFileUri = uri
        viewModelScope.launch {
            val metadata = documentReader.getFileMetadata(uri)
            _state.value = FilePickerState.FileSelected(
                fileUri = uri,
                fileName = metadata.name,
                fileSize = metadata.size,
                mimeType = metadata.mimeType
            )

            // Try to read content for preview
            readFileContent(uri, metadata.mimeType)
        }
    }

    /**
     * Reads file content for preview and later upload.
     */
    private suspend fun readFileContent(uri: Uri, mimeType: String) {
        val content = documentReader.readDocument(uri, mimeType)
        currentFileContent = content.text

        if (content.text != null) {
            val preview = content.text.take(500) + if (content.text.length > 500) "..." else ""
            _state.value = (_state.value as? FilePickerState.FileSelected)?.copy(
                preview = preview
            ) ?: _state.value
        }
    }

    /**
     * Uploads the selected file to the AI gateway.
     */
    fun uploadFile() {
        val uri = currentFileUri ?: return
        val state = _state.value as? FilePickerState.FileSelected ?: return

        val content = currentFileContent
        if (content != null) {
            // Upload extracted text content
            fileUploadManager.uploadTextContent(content, state.fileName)
                .onEach { progress ->
                    handleUploadProgress(progress)
                }
                .catch { e ->
                    _state.value = FilePickerState.Error(e.message ?: "Upload failed")
                }
                .launchIn(viewModelScope)
        } else {
            // Upload raw file
            fileUploadManager.uploadFile(uri, state.fileName, state.mimeType)
                .onEach { progress ->
                    handleUploadProgress(progress)
                }
                .catch { e ->
                    _state.value = FilePickerState.Error(e.message ?: "Upload failed")
                }
                .launchIn(viewModelScope)
        }
    }

    private suspend fun handleUploadProgress(progress: UploadProgress) {
        when (progress) {
            is UploadProgress.Started -> {
                _state.value = FilePickerState.Uploading(fileName = progress.fileName)
            }
            is UploadProgress.InProgress -> {
                _state.value = FilePickerState.Uploading(
                    fileName = progress.fileName,
                    progress = progress.progress
                )
            }
            is UploadProgress.Complete -> {
                _state.value = FilePickerState.Complete(
                    fileName = progress.fileName,
                    response = progress.response
                )
                _events.emit(FilePickerEvent.FileUploaded)
            }
            is UploadProgress.Error -> {
                _state.value = FilePickerState.Error(progress.message)
                _events.emit(FilePickerEvent.ShowError(progress.message))
            }
        }
    }

    /**
     * Resets state for picking a new file.
     */
    fun reset() {
        currentFileUri = null
        currentFileContent = null
        _state.value = FilePickerState.Idle
    }
}
