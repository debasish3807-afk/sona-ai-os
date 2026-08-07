package com.sona.ai.features.beta

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.features.beta.diagnostics.DeviceInfoCollector
import com.sona.ai.features.beta.diagnostics.LogExporter
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DiagnosticsState(
    val deviceInfo: Map<String, String> = emptyMap(),
    val appInfo: Map<String, String> = emptyMap(),
    val performanceInfo: Map<String, String> = emptyMap(),
    val networkInfo: Map<String, String> = emptyMap(),
    val storageInfo: Map<String, String> = emptyMap()
)

@HiltViewModel
class DiagnosticsViewModel @Inject constructor(
    private val deviceInfo: DeviceInfoCollector,
    private val logExporter: LogExporter
) : ViewModel() {

    private val _state = MutableStateFlow(DiagnosticsState())
    val state: StateFlow<DiagnosticsState> = _state.asStateFlow()

    init {
        loadDiagnostics()
    }

    private fun loadDiagnostics() {
        viewModelScope.launch {
            _state.value = DiagnosticsState(
                deviceInfo = deviceInfo.getDeviceMap(),
                appInfo = deviceInfo.getAppMap(),
                performanceInfo = deviceInfo.getPerformanceMap(),
                networkInfo = deviceInfo.getNetworkMap(),
                storageInfo = deviceInfo.getStorageMap()
            )
        }
    }

    fun exportLogs() {
        viewModelScope.launch {
            logExporter.exportToFile()
        }
    }
}
