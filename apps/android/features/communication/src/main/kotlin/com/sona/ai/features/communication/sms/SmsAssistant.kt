package com.sona.ai.features.communication.sms

import javax.inject.Inject
import javax.inject.Singleton

data class SmsMessage(
    val sender: String,
    val body: String,
    val timestamp: Long,
    val isOtp: Boolean = false,
    val isSpam: Boolean = false
)

@Singleton
class SmsAssistant @Inject constructor() {
    private val otpPattern = Regex("\\b\\d{4,8}\\b")
    private val spamKeywords = listOf(
        "win", "prize", "click here", "limited time",
        "act now", "congratulations", "selected"
    )

    fun detectOtp(message: String): String? = otpPattern.find(message)?.value

    fun isSpam(message: String): Boolean =
        spamKeywords.any { message.contains(it, ignoreCase = true) }

    fun classifyMessage(sender: String, body: String): SmsMessage =
        SmsMessage(
            sender = sender,
            body = body,
            timestamp = System.currentTimeMillis(),
            isOtp = detectOtp(body) != null,
            isSpam = isSpam(body)
        )

    fun generateReply(message: String): String = when {
        message.contains("?") -> "Let me think about that and get back to you."
        message.contains("thanks", ignoreCase = true) -> "You're welcome!"
        else -> "Got it, thanks for letting me know."
    }
}
