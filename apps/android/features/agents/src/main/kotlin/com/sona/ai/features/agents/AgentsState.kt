package com.sona.ai.features.agents

/**
 * UI state for the agents screen.
 */
sealed interface AgentsState {

    /** Loading available agents. */
    data object Loading : AgentsState

    /** Agents loaded and ready for execution. */
    data class Success(
        val agents: List<AgentInfo> = emptyList(),
        val runningAgent: AgentExecution? = null
    ) : AgentsState

    /** Error state. */
    data class Error(
        val message: String
    ) : AgentsState
}

/**
 * Information about an available AI agent.
 */
data class AgentInfo(
    val id: String,
    val name: String,
    val description: String,
    val type: AgentType,
    val capabilities: List<String> = emptyList(),
    val isAvailable: Boolean = true
)

/**
 * Types of AI agents available.
 */
enum class AgentType(val label: String, val icon: String) {
    RESEARCH("Research", "search"),
    CODE("Code", "code"),
    WRITING("Writing", "edit_note"),
    PLANNING("Planning", "task_alt"),
    DATA("Data Analysis", "analytics"),
    AUTOMATION("Automation", "smart_toy")
}

/**
 * Represents a running agent execution.
 */
data class AgentExecution(
    val agentId: String,
    val agentName: String,
    val status: ExecutionStatus,
    val progress: Float = 0f,
    val steps: List<AgentStep> = emptyList(),
    val result: String? = null
)

/**
 * Status of agent execution.
 */
enum class ExecutionStatus {
    QUEUED,
    RUNNING,
    COMPLETED,
    FAILED,
    CANCELLED
}

/**
 * A single step in agent execution.
 */
data class AgentStep(
    val id: String,
    val description: String,
    val status: ExecutionStatus,
    val output: String? = null,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * One-time UI events for the agents screen.
 */
sealed interface AgentsEvent {
    data class ShowError(val message: String) : AgentsEvent
    data class AgentCompleted(val agentId: String, val result: String) : AgentsEvent
    data class AgentFailed(val agentId: String, val error: String) : AgentsEvent
}
