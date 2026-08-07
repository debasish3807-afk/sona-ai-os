package com.sona.ai.data.remote

import javax.inject.Inject
import javax.inject.Singleton

/**
 * API interface for file uploads to the Sona AI gateway.
 * Handles multipart file uploads and text content uploads.
 */
@Singleton
class FileUploadApi @Inject constructor(
    private val sonaApi: SonaApi
) {

    /**
     * Uploads a file with binary content.
     * @param fileName Name of the file being uploaded
     * @param mimeType MIME type of the file
     * @param fileContent Raw file bytes
     * @return AI response/analysis of the file content
     */
    suspend fun uploadFile(
        fileName: String,
        mimeType: String,
        fileContent: ByteArray
    ): String {
        val response = sonaApi.uploadFile(
            fileName = fileName,
            mimeType = mimeType,
            content = fileContent
        )
        return response.analysis
    }

    /**
     * Uploads extracted text content from a document.
     * @param content The text content to send to AI
     * @param fileName Original file name for context
     * @return AI response/analysis
     */
    suspend fun uploadTextContent(
        content: String,
        fileName: String
    ): String {
        val response = sonaApi.uploadTextContent(
            fileName = fileName,
            content = content
        )
        return response.analysis
    }

    /**
     * Uploads an image for AI analysis.
     * @param imagePath Path or URI string of the image
     * @return AI description/analysis of the image
     */
    suspend fun uploadImage(imagePath: String): String {
        val response = sonaApi.analyzeImage(imagePath = imagePath)
        return response.analysis
    }
}
