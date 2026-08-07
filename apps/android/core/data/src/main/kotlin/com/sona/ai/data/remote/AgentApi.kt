package com.sona.ai.data.remote

import javax.inject.Inject
import javax.inject.Singleton

/**
 * API interface for AI agent operations.
 * Manages listing, executing, and monitoring agent tasks.
 */
@Singleton
class AgentApi @Inject constructor(
    private val sonaApi: SonaApi
) {

    /**
     * Lists all available AI agents.
     */
    suspend fun listAgents(): List<AgentDto> {
        return sonaApi.getAgents()
    }

    /**
     * Starts an agent execution with the given prompt.
     * @return Execution ID for polling status
     */
    suspend fun executeAgent(agentId: String, prompt: String): String {
        val response = sonaApi.executeAgent(
            agentId = agentId,
            request = AgentExecuteRequest(prompt = prompt)
        )
        return response.executionId
    }

    /**
     * Gets the current status of an agent execution.
     */
    suspend fun getExecutionStatus(executionId: String): AgentExecutionStatusDto {
        return sonaApi.getAgentExecutionStatus(executionId)
    }

    /**
     * Cancels a running agent execution.
     */
    suspend fun cancelExecution(executionId: String) {
        sonaApi.cancelAgentExecution(executionId)
    }
}

/**
 * DTO for an available agent.
 */
data class AgentDto(
    val id: String,
    val name: String,
    val description: String,
    val type: String,
    val capabilities: List<String>,
    val isAvailable: Boolean
)

/**
 * Request body for executing an agent.
 */
data class AgentExecuteRequest(
    val prompt: String
)

/**
 * Response from agent execution start.
 */
data class AgentExecuteResponse(
    val executionId: String
)

/**
 * DTO for agent execution status.
 */
data class AgentExecutionStatusDto(
    val executionId: String,
    val status: String,
    val progress: Float,
    val steps: List<AgentStepDto>,
    val result: String?
)

/**
 * DTO for a single agent execution step.
 */
data class AgentStepDto(
    val id: String,
    val description: String,
    val status: String,
    val output: String?,
    val timestamp: Long
)
