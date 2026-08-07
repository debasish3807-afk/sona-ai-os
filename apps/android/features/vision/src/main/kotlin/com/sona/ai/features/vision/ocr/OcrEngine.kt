package com.sona.ai.features.vision.ocr

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.TextRecognizer
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.sona.ai.features.vision.OcrOutput
import com.sona.ai.features.vision.TextBlock
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * OCR engine powered by ML Kit text recognition.
 * Provides text extraction from images and bitmaps using on-device ML.
 */
@Singleton
class OcrEngine @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val recognizer: TextRecognizer =
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    /**
     * Extract text from an image URI.
     *
     * @param imageUri URI pointing to the image file
     * @return [OcrOutput] containing extracted text, confidence, and text blocks
     * @throws Exception if ML Kit processing fails
     */
    suspend fun extractText(imageUri: Uri): OcrOutput = suspendCancellableCoroutine { cont ->
        val image = InputImage.fromFilePath(context, imageUri)
        recognizer.process(image)
            .addOnSuccessListener { visionText ->
                val blocks = visionText.textBlocks.map { block ->
                    TextBlock(
                        text = block.text,
                        boundingBox = block.boundingBox?.toShortString() ?: "",
                        confidence = 0.9f
                    )
                }
                cont.resume(
                    OcrOutput(
                        text = visionText.text,
                        confidence = 0.95f,
                        blocks = blocks
                    )
                )
            }
            .addOnFailureListener { e ->
                cont.resumeWithException(e)
            }
    }

    /**
     * Extract text from a Bitmap (used for PDF page rendering).
     *
     * @param bitmap The bitmap image to process
     * @return [OcrOutput] containing extracted text and confidence
     * @throws Exception if ML Kit processing fails
     */
    suspend fun extractFromBitmap(bitmap: Bitmap): OcrOutput = suspendCancellableCoroutine { cont ->
        val image = InputImage.fromBitmap(bitmap, 0)
        recognizer.process(image)
            .addOnSuccessListener { visionText ->
                val blocks = visionText.textBlocks.map { block ->
                    TextBlock(
                        text = block.text,
                        boundingBox = block.boundingBox?.toShortString() ?: "",
                        confidence = 0.9f
                    )
                }
                cont.resume(
                    OcrOutput(
                        text = visionText.text,
                        confidence = 0.95f,
                        blocks = blocks
                    )
                )
            }
            .addOnFailureListener { e ->
                cont.resumeWithException(e)
            }
    }
}
