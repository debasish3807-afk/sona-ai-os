package com.sona.ai.features.voice.commands

import com.sona.ai.domain.repository.ChatRepository
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Contextual information passed to command handlers.
 */
data class CommandContext(
    val history: List<String> = emptyList(),
    val lastResponse: String = ""
)

/**
 * Routes voice commands to appropriate handlers.
 * First checks against built-in commands, then falls back to AI chat.
 */
@Singleton
class VoiceCommandRouter @Inject constructor(
    private val chatRepository: ChatRepository
) {

    private val builtinCommands = mapOf<String, suspend (String) -> String>(
        "what time is it" to { _ ->
            "The current time is ${
                java.time.LocalTime.now().format(
                    java.time.format.DateTimeFormatter.ofPattern("h:mm a")
                )
            }"
        },
        "stop" to { _ -> "Stopping." },
        "cancel" to { _ -> "Cancelled." },
        "repeat" to { ctx -> ctx }
    )

    /**
     * Routes the input to the appropriate handler.
     * Built-in commands are matched first by prefix, then falls back to AI.
     *
     * @param input The user's voice input text
     * @param context Contextual information from the conversation
     * @return The response string
     */
    suspend fun route(input: String, context: CommandContext): String {
        val lowered = input.lowercase().trim()

        // Check built-in commands first
        builtinCommands.entries.firstOrNull { lowered.startsWith(it.key) }?.let {
            return it.value(context.lastResponse)
        }

        // Default: send to AI via ChatRepository
        return try {
            val response = chatRepository.sendMessage("voice-session", input)
            response.content
        } catch (e: Exception) {
            "Sorry, I couldn't process that. ${e.message}"
        }
    }
}
