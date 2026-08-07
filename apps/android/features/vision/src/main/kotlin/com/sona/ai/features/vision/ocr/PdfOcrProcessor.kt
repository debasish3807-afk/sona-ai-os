package com.sona.ai.features.vision.ocr

import android.content.Context
import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import com.sona.ai.features.vision.OcrOutput
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Processor for extracting text from PDF documents using PdfRenderer + OCR.
 * Renders each PDF page to a bitmap and then runs ML Kit text recognition.
 */
@Singleton
class PdfOcrProcessor @Inject constructor(
    @ApplicationContext private val context: Context,
    private val ocrEngine: OcrEngine
) {
    /**
     * Extract text from all pages of a PDF document.
     *
     * @param pdfUri URI pointing to the PDF file
     * @return [OcrOutput] with combined text from all pages
     * @throws IllegalStateException if the PDF cannot be opened
     */
    suspend fun extractFromPdf(pdfUri: Uri): OcrOutput = withContext(Dispatchers.IO) {
        val descriptor = context.contentResolver.openFileDescriptor(pdfUri, "r")
            ?: throw IllegalStateException("Cannot open PDF file")

        val renderer = PdfRenderer(descriptor)
        val allText = StringBuilder()
        val pageCount = renderer.pageCount

        for (i in 0 until pageCount) {
            val page = renderer.openPage(i)
            val bitmap = Bitmap.createBitmap(
                page.width * 2,
                page.height * 2,
                Bitmap.Config.ARGB_8888
            )
            page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)

            val pageResult = ocrEngine.extractFromBitmap(bitmap)
            allText.append(pageResult.text).append("\n\n")

            bitmap.recycle()
            page.close()
        }

        renderer.close()
        descriptor.close()

        OcrOutput(
            text = allText.toString().trim(),
            confidence = 0.9f
        )
    }
}
