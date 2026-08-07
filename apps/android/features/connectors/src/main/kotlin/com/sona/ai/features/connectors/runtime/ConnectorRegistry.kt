package com.sona.ai.features.connectors.runtime

import javax.inject.Inject
import javax.inject.Singleton

/**
 * Registry that manages all available connectors in the system.
 * Connectors are registered at startup and can be queried by ID
 * or filtered by connection status.
 */
@Singleton
class ConnectorRegistry @Inject constructor() {

    private val connectors = mutableMapOf<String, Connector>()

    /** Register a new connector */
    fun register(connector: Connector) {
        connectors[connector.id] = connector
    }

    /** Get a connector by its unique ID */
    fun get(id: String): Connector? = connectors[id]

    /** List all registered connectors */
    fun listAll(): List<Connector> = connectors.values.toList()

    /** List only currently connected connectors */
    fun getConnected(): List<Connector> = connectors.values.filter { it.isConnected }
}
