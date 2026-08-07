package com.sona.ai.features.communication.calling

import javax.inject.Inject
import javax.inject.Singleton

data class CallRecord(
    val contactName: String,
    val number: String,
    val duration: Long,
    val type: CallType,
    val timestamp: Long,
    val notes: String = ""
)

enum class CallType { INCOMING, OUTGOING, MISSED }

@Singleton
class CallingAssistant @Inject constructor() {
    private val calls = mutableListOf<CallRecord>()

    fun addCall(call: CallRecord) {
        calls.add(call)
    }

    fun getMissedCallCount(): Int = calls.count { it.type == CallType.MISSED }

    fun generateCallNotes(callId: String): String =
        "Call with ${calls.lastOrNull()?.contactName ?: "Unknown"}. Duration: ${calls.lastOrNull()?.duration ?: 0}s."

    fun suggestFollowUp(call: CallRecord): List<String> = listOf(
        "Send a follow-up message to ${call.contactName}",
        "Schedule a callback",
        "Add to contacts if new"
    )

    fun generateSummary(): String {
        val missed = calls.count { it.type == CallType.MISSED }
        val incoming = calls.count { it.type == CallType.INCOMING }
        return "$missed missed call(s), $incoming incoming call(s) today."
    }

    fun getCallerIntelligence(number: String): String =
        calls.filter { it.number == number }.let { history ->
            if (history.isEmpty()) "Unknown caller"
            else "Known contact: ${history.first().contactName}. ${history.size} previous call(s)."
        }
}
