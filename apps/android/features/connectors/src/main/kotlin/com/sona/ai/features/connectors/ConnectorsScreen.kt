package com.sona.ai.features.connectors

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

/**
 * Main Connectors hub screen showing all available integrations
 * and their connection status. Users can connect, disconnect, and sync
 * individual connectors from this screen.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectorsScreen(
    onNavigateBack: () -> Unit = {},
    viewModel: ConnectorsViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Connectors") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        if (state.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(state.connectors) { connector ->
                    ConnectorCard(
                        connector = connector,
                        onConnect = { viewModel.connect(connector.id) },
                        onDisconnect = { viewModel.disconnect(connector.id) },
                        onSync = { viewModel.sync(connector.id) }
                    )
                }
            }
        }
    }
}

/**
 * Individual card for a connector showing its status and action buttons.
 */
@Composable
private fun ConnectorCard(
    connector: ConnectorInfo,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit,
    onSync: () -> Unit
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Icon(
                    imageVector = if (connector.connected) Icons.Default.CheckCircle else Icons.Default.CloudOff,
                    contentDescription = connector.name,
                    tint = if (connector.connected) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.outline
                    }
                )
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = connector.name,
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = if (connector.connected) {
                            "Connected • ${connector.lastSync}"
                        } else {
                            "Not connected"
                        },
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }

            Spacer(Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (connector.connected) {
                    OutlinedButton(onClick = onSync) {
                        Text("Sync")
                    }
                    OutlinedButton(onClick = onDisconnect) {
                        Text("Disconnect")
                    }
                } else {
                    Button(onClick = onConnect) {
                        Text("Connect")
                    }
                }
            }
        }
    }
}
