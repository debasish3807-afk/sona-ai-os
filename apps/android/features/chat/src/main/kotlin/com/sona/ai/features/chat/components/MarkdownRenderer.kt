package com.sona.ai.features.chat.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Simple markdown renderer for chat messages.
 * Handles code blocks, bold, italic, and headers.
 */
@Composable
fun MarkdownRenderer(
    content: String,
    isUser: Boolean,
    modifier: Modifier = Modifier
) {
    val textColor = if (isUser) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onSecondaryContainer
    }

    Column(modifier = modifier) {
        val parts = content.split("```")

        parts.forEachIndexed { index, part ->
            if (index % 2 == 0) {
                // Regular text - render with basic markdown
                if (part.isNotBlank()) {
                    val lines = part.trim().lines()
                    lines.forEach { line ->
                        when {
                            line.startsWith("### ") -> {
                                Text(
                                    text = line.removePrefix("### "),
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = textColor
                                )
                            }
                            line.startsWith("## ") -> {
                                Text(
                                    text = line.removePrefix("## "),
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = textColor
                                )
                            }
                            line.startsWith("# ") -> {
                                Text(
                                    text = line.removePrefix("# "),
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = textColor
                                )
                            }
                            line.isNotBlank() -> {
                                Text(
                                    text = line,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = textColor
                                )
                            }
                        }
                    }
                }
            } else {
                // Code block
                Spacer(modifier = Modifier.height(4.dp))
                val codeContent = part.trimStart()
                val language = codeContent.lines().firstOrNull()?.takeIf { !it.contains(" ") } ?: ""
                val code = if (language.isNotEmpty()) {
                    codeContent.removePrefix(language).trim()
                } else {
                    codeContent.trim()
                }
                CodeBlock(code = code, language = language)
                Spacer(modifier = Modifier.height(4.dp))
            }
        }
    }
}
