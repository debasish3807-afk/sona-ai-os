package com.sona.ai.features.communication.email

import javax.inject.Inject
import javax.inject.Singleton

data class EmailSummary(
    val sender: String,
    val subject: String,
    val preview: String,
    val isImportant: Boolean,
    val category: EmailCategory
)

enum class EmailCategory { PRIMARY, SOCIAL, PROMOTIONS, UPDATES, FORUMS }

@Singleton
class EmailAssistant @Inject constructor() {
    private val emails = mutableListOf<EmailSummary>()

    fun addEmail(email: EmailSummary) {
        emails.add(email)
    }

    fun getUnreadCount(): Int = emails.size

    fun classifyEmail(sender: String, subject: String): EmailCategory = when {
        sender.contains("noreply", ignoreCase = true) ||
            subject.contains("newsletter", ignoreCase = true) -> EmailCategory.PROMOTIONS
        sender.contains("github", ignoreCase = true) ||
            sender.contains("jira", ignoreCase = true) -> EmailCategory.UPDATES
        subject.contains("social", ignoreCase = true) ||
            sender.contains("facebook", ignoreCase = true) -> EmailCategory.SOCIAL
        else -> EmailCategory.PRIMARY
    }

    fun isImportant(sender: String, subject: String): Boolean =
        subject.contains("urgent", ignoreCase = true) ||
            subject.contains("action required", ignoreCase = true) ||
            subject.contains("deadline", ignoreCase = true)

    fun generateReplyDraft(email: EmailSummary): String =
        "Hi,\n\nThank you for your email regarding \"${email.subject}\". I'll review this and get back to you shortly.\n\nBest regards"

    fun generateSummary(): String =
        if (emails.isEmpty()) "No unread emails."
        else "${emails.size} unread. ${emails.count { it.isImportant }} important. Categories: ${
            emails.groupBy { it.category }.map { "${it.key}: ${it.value.size}" }.joinToString(", ")
        }"
}
