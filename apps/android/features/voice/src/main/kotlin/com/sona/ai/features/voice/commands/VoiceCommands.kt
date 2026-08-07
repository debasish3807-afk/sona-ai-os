package com.sona.ai.features.voice.commands

/**
 * Types of voice commands that can be recognized and routed.
 */
enum class VoiceCommandType {
    CHAT,
    SEARCH,
    REMEMBER,
    FORGET,
    READ,
    SUMMARIZE,
    NAVIGATE,
    SYSTEM
}

/**
 * A parsed voice command with its type, payload, and confidence level.
 */
data class ParsedCommand(
    val type: VoiceCommandType,
    val payload: String,
    val confidence: Float = 1f
)

/**
 * Parses raw voice input into structured command objects.
 * Uses keyword-based prefix matching to determine command intent.
 */
class VoiceCommandParser {

    /**
     * Parses the input string into a [ParsedCommand].
     * Matches command prefixes and extracts the payload.
     */
    fun parse(input: String): ParsedCommand {
        val lowered = input.lowercase()
        return when {
            lowered.startsWith("search") || lowered.startsWith("find") ->
                ParsedCommand(VoiceCommandType.SEARCH, input.substringAfter(" "))

            lowered.startsWith("remember") || lowered.startsWith("save") ->
                ParsedCommand(VoiceCommandType.REMEMBER, input.substringAfter(" "))

            lowered.startsWith("forget") ->
                ParsedCommand(VoiceCommandType.FORGET, input.substringAfter(" "))

            lowered.startsWith("read") ->
                ParsedCommand(VoiceCommandType.READ, input.substringAfter(" "))

            lowered.startsWith("summarize") || lowered.startsWith("summary") ->
                ParsedCommand(VoiceCommandType.SUMMARIZE, input.substringAfter(" "))

            lowered.startsWith("go to") || lowered.startsWith("open") ->
                ParsedCommand(VoiceCommandType.NAVIGATE, input.substringAfter(" "))

            lowered.startsWith("set") || lowered.startsWith("turn") ->
                ParsedCommand(VoiceCommandType.SYSTEM, input)

            else ->
                ParsedCommand(VoiceCommandType.CHAT, input)
        }
    }
}
