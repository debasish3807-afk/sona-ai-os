package com.sona.ai.features.beta.diagnostics

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LogExporter @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val logs = mutableListOf<String>()
    private val maxLogs = 500

    fun log(tag: String, message: String) {
        logs.add("[${timestamp()}] [$tag] $message")
        if (logs.size > maxLogs) logs.removeAt(0)
    }

    fun exportRecent(): String = logs.takeLast(100).joinToString("\n")

    fun exportToFile(): File {
        val file = File(context.cacheDir, "sona_logs_${System.currentTimeMillis()}.txt")
        file.writeText(logs.joinToString("\n"))
        return file
    }

    fun clear() {
        logs.clear()
    }

    private fun timestamp(): String =
        SimpleDateFormat("HH:mm:ss.SSS", Locale.US).format(Date())
}
