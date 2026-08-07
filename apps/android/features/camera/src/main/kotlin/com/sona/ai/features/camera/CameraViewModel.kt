package com.sona.ai.features.camera

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.data.remote.FileUploadApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Camera feature.
 * Handles capture → preview → upload → AI response flow.
 */
@HiltViewModel
class CameraViewModel @Inject constructor(
    private val fileUploadApi: FileUploadApi
) : ViewModel() {

    private val _state = MutableStateFlow<CameraState>(CameraState.Preview)
    val state: StateFlow<CameraState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<CameraEvent>()
    val events: SharedFlow<CameraEvent> = _events.asSharedFlow()

    /**
     * Called when an image is captured from the camera.
     */
    fun onImageCaptured(uri: Uri) {
        _state.value = CameraState.ImageCaptured(
            imageUri = uri,
            source = ImageSource.CAMERA
        )
    }

    /**
     * Called when an image is selected from the gallery.
     */
    fun onImageSelected(uri: Uri?) {
        if (uri != null) {
            _state.value = CameraState.ImageCaptured(
                imageUri = uri,
                source = ImageSource.GALLERY
            )
        }
    }

    /**
     * Uploads the captured image to the AI gateway for analysis.
     */
    fun sendImage() {
        val currentState = _state.value
        if (currentState !is CameraState.ImageCaptured) return

        _state.value = CameraState.Uploading(imageUri = currentState.imageUri)

        viewModelScope.launch {
            try {
                val response = fileUploadApi.uploadImage(currentState.imageUri.toString())
                _state.value = CameraState.Complete(
                    imageUri = currentState.imageUri,
                    aiResponse = response
                )
                _events.emit(CameraEvent.ImageSent)
            } catch (e: Exception) {
                _state.value = CameraState.Error(
                    message = e.message ?: "Failed to upload image",
                    imageUri = currentState.imageUri
                )
                _events.emit(CameraEvent.ShowError(e.message ?: "Upload failed"))
            }
        }
    }

    /**
     * Discards the current image and returns to preview.
     */
    fun discardImage() {
        _state.value = CameraState.Preview
    }

    /**
     * Resets state back to camera preview.
     */
    fun resetToPreview() {
        _state.value = CameraState.Preview
    }
}
