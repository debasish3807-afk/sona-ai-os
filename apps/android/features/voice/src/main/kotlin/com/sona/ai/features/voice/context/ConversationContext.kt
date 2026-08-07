package com.sona.ai.features.voice.context

import com.sona.ai.features.voice.commands.CommandContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Represents a single turn in the conversation between user and assistant.
 */
data class ConversationTurn(
    val userInput: String,
    val assistantResponse: String,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Maintains the conversational state for the voice assistant.
 * Keeps a rolling window of recent conversation turns to provide
 * context to the command router and AI backend.
 */
@Singleton
class ConversationContext @Inject constructor() {

    private val turns = mutableListOf<ConversationTurn>()
    private val maxTurns = 20

    /**
     * Adds a new conversation turn.
     * Automatically evicts the oldest turn if the maximum is exceeded.
     */
    fun addTurn(input: String, response: String) {
        turns.add(ConversationTurn(input, response))
        if (turns.size > maxTurns) {
            turns.removeAt(0)
        }
    }

    /**
     * Gets the current command context for the voice command router.
     */
    fun getContext(): CommandContext = CommandContext(
        history = turns.map { it.userInput },
        lastResponse = turns.lastOrNull()?.assistantResponse ?: ""
    )

    /**
     * Returns the full conversation history.
     */
    fun getHistory(): List<ConversationTurn> = turns.toList()

    /**
     * Clears all conversation history.
     */
    fun clear() {
        turns.clear()
    }

    /**
     * Returns the last assistant response, or empty string if none.
     */
    fun getLastResponse(): String =
        turns.lastOrNull()?.assistantResponse ?: ""

    /**
     * Returns the number of turns in the current conversation.
     */
    fun turnCount(): Int = turns.size
}
