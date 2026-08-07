package com.sona.ai.features.connectors.runtime

/**
 * Base interface for all connectors in the Sona AI system.
 * Each connector represents an external service integration
 * (e.g., GitHub, Google, Slack) that can be connected, disconnected,
 * and synced.
 */
interface Connector {
    /** Unique identifier for this connector */
    val id: String

    /** Human-readable display name */
    val name: String

    /** Whether this connector currently has active credentials */
    val isConnected: Boolean

    /** Initiate the connection/authentication flow */
    suspend fun connect(): Boolean

    /** Revoke credentials and disconnect */
    suspend fun disconnect()

    /** Perform a data sync with the external service */
    suspend fun sync(): SyncResult

    /** Check if the connector is healthy and credentials are valid */
    suspend fun healthCheck(): Boolean
}

/**
 * Result of a sync operation containing success status,
 * item count, any errors, and timestamp.
 */
data class SyncResult(
    val success: Boolean,
    val itemsSynced: Int = 0,
    val errors: List<String> = emptyList(),
    val lastSync: Long = System.currentTimeMillis()
)
