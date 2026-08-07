package com.sona.ai.features.connectors.runtime

import com.sona.ai.features.connectors.ConnectorInfo
import javax.inject.Inject
import javax.inject.Singleton

/**
 * High-level orchestrator for all connector operations.
 * Provides a unified API for the ViewModel/UI layer to interact
 * with connectors, handling delegation to the sync engine,
 * registry, and token manager.
 */
@Singleton
class ConnectorManager @Inject constructor(
    private val registry: ConnectorRegistry,
    private val syncEngine: SyncEngine,
    private val tokenManager: TokenManager
) {

    /** List all connectors with their current status as UI-friendly ConnectorInfo */
    fun listConnectors(): List<ConnectorInfo> {
        return registry.listAll().map { connector ->
            ConnectorInfo(
                id = connector.id,
                name = connector.name,
                connected = connector.isConnected,
                lastSync = "",
                itemCount = 0
            )
        }
    }

    /** Initiate connection for a specific connector */
    suspend fun connect(connectorId: String): Boolean {
        return registry.get(connectorId)?.connect() ?: false
    }

    /** Disconnect a connector and clear its stored tokens */
    suspend fun disconnect(connectorId: String) {
        registry.get(connectorId)?.disconnect()
        tokenManager.clearToken(connectorId)
    }

    /** Sync a specific connector through the sync engine (with retry) */
    suspend fun sync(connectorId: String): SyncResult {
        return registry.get(connectorId)?.let { connector ->
            syncEngine.sync(connector)
        } ?: SyncResult(success = false, errors = listOf("Connector not found"))
    }

    /** Sync all currently connected connectors */
    suspend fun syncAll(): List<SyncResult> {
        return registry.getConnected().map { connector ->
            syncEngine.sync(connector)
        }
    }
}
