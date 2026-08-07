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

data class FeedbackState(
    val submitted: Boolean = false,
    val isSubmitting: Boolean = false
)

@HiltViewModel
class FeedbackViewModel @Inject constructor(
    private val deviceInfo: DeviceInfoCollector,
    private val logExporter: LogExporter,
    private val feedbackRepository: FeedbackRepository
) : ViewModel() {

    private val _state = MutableStateFlow(FeedbackState())
    val state: StateFlow<FeedbackState> = _state.asStateFlow()

    fun submit(type: String, description: String, includeDevice: Boolean, includeLogs: Boolean) {
        viewModelScope.launch {
            _state.value = FeedbackState(isSubmitting = true)
            val report = FeedbackReport(
                type = type,
                description = description,
                deviceInfo = if (includeDevice) deviceInfo.collect() else null,
                logs = if (includeLogs) logExporter.exportRecent() else null,
                timestamp = System.currentTimeMillis()
            )
            feedbackRepository.submit(report)
            _state.value = FeedbackState(submitted = true)
        }
    }
}
