package com.sona.ai.features.connectors

/**
 * Represents a single connector service configuration and status.
 */
data class ConnectorInfo(
    val id: String,
    val name: String,
    val connected: Boolean,
    val lastSync: String = "",
    val itemCount: Int = 0
)

/**
 * UI state for the Connectors screen.
 */
data class ConnectorsState(
    val connectors: List<ConnectorInfo> = emptyList(),
    val isLoading: Boolean = false
)
