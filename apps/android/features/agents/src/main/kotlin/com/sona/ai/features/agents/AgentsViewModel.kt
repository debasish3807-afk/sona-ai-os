package com.sona.ai.features.agents

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.data.remote.AgentApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the agents screen.
 * Manages listing, executing, and monitoring agents.
 */
@HiltViewModel
class AgentsViewModel @Inject constructor(
    private val agentApi: AgentApi
) : ViewModel() {

    private val _state = MutableStateFlow<AgentsState>(AgentsState.Loading)
    val state: StateFlow<AgentsState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<AgentsEvent>()
    val events: SharedFlow<AgentsEvent> = _events.asSharedFlow()

    private var pollingJob: Job? = null

    init {
        loadAgents()
    }

    /**
     * Loads available agents from the API.
     */
    private fun loadAgents() {
        viewModelScope.launch {
            try {
                val agents = agentApi.listAgents()
                _state.value = AgentsState.Success(
                    agents = agents.map { dto ->
                        AgentInfo(
                            id = dto.id,
                            name = dto.name,
                            description = dto.description,
                            type = AgentType.valueOf(dto.type.uppercase()),
                            capabilities = dto.capabilities,
                            isAvailable = dto.isAvailable
                        )
                    }
                )
            } catch (e: Exception) {
                _state.value = AgentsState.Error(e.message ?: "Failed to load agents")
            }
        }
    }

    /**
     * Executes an agent with the given prompt.
     */
    fun executeAgent(agentId: String, prompt: String) {
        val currentState = _state.value as? AgentsState.Success ?: return
        val agent = currentState.agents.find { it.id == agentId } ?: return

        val execution = AgentExecution(
            agentId = agentId,
            agentName = agent.name,
            status = ExecutionStatus.QUEUED,
            progress = 0f
        )

        _state.update { current ->
            if (current is AgentsState.Success) {
                current.copy(runningAgent = execution)
            } else current
        }

        viewModelScope.launch {
            try {
                val executionId = agentApi.executeAgent(agentId, prompt)
                _state.update { current ->
                    if (current is AgentsState.Success) {
                        current.copy(
                            runningAgent = execution.copy(status = ExecutionStatus.RUNNING)
                        )
                    } else current
                }
                startPolling(executionId)
            } catch (e: Exception) {
                _state.update { current ->
                    if (current is AgentsState.Success) {
                        current.copy(
                            runningAgent = execution.copy(
                                status = ExecutionStatus.FAILED,
                                result = e.message
                            )
                        )
                    } else current
                }
                _events.emit(AgentsEvent.AgentFailed(agentId, e.message ?: "Execution failed"))
            }
        }
    }

    /**
     * Polls agent execution status until completion.
     */
    private fun startPolling(executionId: String) {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (true) {
                delay(2000) // Poll every 2 seconds
                try {
                    val status = agentApi.getExecutionStatus(executionId)
                    _state.update { current ->
                        if (current is AgentsState.Success && current.runningAgent != null) {
                            current.copy(
                                runningAgent = current.runningAgent.copy(
                                    status = ExecutionStatus.valueOf(status.status.uppercase()),
                                    progress = status.progress,
                                    steps = status.steps.map { step ->
                                        AgentStep(
                                            id = step.id,
                                            description = step.description,
                                            status = ExecutionStatus.valueOf(step.status.uppercase()),
                                            output = step.output,
                                            timestamp = step.timestamp
                                        )
                                    },
                                    result = status.result
                                )
                            )
                        } else current
                    }

                    if (status.status.uppercase() in listOf("COMPLETED", "FAILED", "CANCELLED")) {
                        val currentState = _state.value as? AgentsState.Success
                        currentState?.runningAgent?.let { agent ->
                            if (agent.status == ExecutionStatus.COMPLETED) {
                                _events.emit(AgentsEvent.AgentCompleted(agent.agentId, agent.result ?: ""))
                            }
                        }
                        break
                    }
                } catch (e: Exception) {
                    // Continue polling on transient errors
                }
            }
        }
    }

    /**
     * Cancels a running agent execution.
     */
    fun cancelExecution() {
        pollingJob?.cancel()
        _state.update { current ->
            if (current is AgentsState.Success) {
                current.copy(
                    runningAgent = current.runningAgent?.copy(status = ExecutionStatus.CANCELLED)
                )
            } else current
        }
    }

    /**
     * Dismisses the execution result.
     */
    fun dismissResult() {
        _state.update { current ->
            if (current is AgentsState.Success) {
                current.copy(runningAgent = null)
            } else current
        }
    }

    /**
     * Refreshes the agent list.
     */
    fun refresh() {
        _state.value = AgentsState.Loading
        loadAgents()
    }

    override fun onCleared() {
        super.onCleared()
        pollingJob?.cancel()
    }
}
