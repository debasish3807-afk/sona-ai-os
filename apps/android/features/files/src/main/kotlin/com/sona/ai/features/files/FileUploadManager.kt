package com.sona.ai.features.files

import android.content.Context
import android.net.Uri
import com.sona.ai.data.remote.FileUploadApi
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Manages file uploads to the AI gateway.
 * Handles multipart uploads with progress tracking.
 */
@Singleton
class FileUploadManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileUploadApi: FileUploadApi
) {

    /**
     * Uploads a file and emits progress updates.
     */
    fun uploadFile(uri: Uri, fileName: String, mimeType: String): Flow<UploadProgress> = flow {
        emit(UploadProgress.Started(fileName))

        try {
            // Read file bytes
            val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                ?: throw IllegalStateException("Cannot read file")

            emit(UploadProgress.InProgress(fileName, 0.3f))

            // Upload via API
            val response = fileUploadApi.uploadFile(
                fileName = fileName,
                mimeType = mimeType,
                fileContent = bytes
            )

            emit(UploadProgress.InProgress(fileName, 0.9f))
            emit(UploadProgress.Complete(fileName, response))
        } catch (e: Exception) {
            emit(UploadProgress.Error(fileName, e.message ?: "Upload failed"))
        }
    }.flowOn(Dispatchers.IO)

    /**
     * Uploads a file with extracted text content (for when direct upload isn't needed).
     */
    fun uploadTextContent(content: String, fileName: String): Flow<UploadProgress> = flow {
        emit(UploadProgress.Started(fileName))

        try {
            val response = fileUploadApi.uploadTextContent(
                content = content,
                fileName = fileName
            )
            emit(UploadProgress.Complete(fileName, response))
        } catch (e: Exception) {
            emit(UploadProgress.Error(fileName, e.message ?: "Upload failed"))
        }
    }.flowOn(Dispatchers.IO)
}

/**
 * Progress updates during file upload.
 */
sealed interface UploadProgress {
    data class Started(val fileName: String) : UploadProgress
    data class InProgress(val fileName: String, val progress: Float) : UploadProgress
    data class Complete(val fileName: String, val response: String) : UploadProgress
    data class Error(val fileName: String, val message: String) : UploadProgress
}
