package com.sona.ai.features.camera

import android.net.Uri

/**
 * UI state for the camera feature screen.
 */
sealed interface CameraState {

    /** Camera preview is active and ready to capture. */
    data object Preview : CameraState

    /** An image has been captured or selected and is being previewed. */
    data class ImageCaptured(
        val imageUri: Uri,
        val source: ImageSource
    ) : CameraState

    /** Image is being uploaded to the AI gateway. */
    data class Uploading(
        val imageUri: Uri,
        val progress: Float = 0f
    ) : CameraState

    /** Upload complete, AI response received. */
    data class Complete(
        val imageUri: Uri,
        val aiResponse: String
    ) : CameraState

    /** An error occurred. */
    data class Error(
        val message: String,
        val imageUri: Uri? = null
    ) : CameraState
}

/**
 * Source of the captured/selected image.
 */
enum class ImageSource {
    CAMERA,
    GALLERY
}

/**
 * One-time UI events for the camera screen.
 */
sealed interface CameraEvent {
    data class ShowError(val message: String) : CameraEvent
    data object CameraPermissionRequired : CameraEvent
    data object ImageSent : CameraEvent
}
