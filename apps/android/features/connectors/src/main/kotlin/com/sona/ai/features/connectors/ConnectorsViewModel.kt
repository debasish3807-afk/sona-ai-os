package com.sona.ai.features.connectors

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.features.connectors.runtime.ConnectorManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Connectors screen. Manages connector state
 * and delegates operations to the ConnectorManager.
 */
@HiltViewModel
class ConnectorsViewModel @Inject constructor(
    private val connectorManager: ConnectorManager
) : ViewModel() {

    private val _state = MutableStateFlow(ConnectorsState())
    val state: StateFlow<ConnectorsState> = _state.asStateFlow()

    init {
        loadConnectors()
    }

    private fun loadConnectors() {
        viewModelScope.launch {
            _state.value = ConnectorsState(
                connectors = connectorManager.listConnectors()
            )
        }
    }

    fun connect(connectorId: String) {
        viewModelScope.launch {
            connectorManager.connect(connectorId)
            loadConnectors()
        }
    }

    fun disconnect(connectorId: String) {
        viewModelScope.launch {
            connectorManager.disconnect(connectorId)
            loadConnectors()
        }
    }

    fun sync(connectorId: String) {
        viewModelScope.launch {
            connectorManager.sync(connectorId)
            loadConnectors()
        }
    }
}
