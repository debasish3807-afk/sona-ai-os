package com.sona.ai.features.communication

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sona.ai.features.communication.calling.CallingAssistant
import com.sona.ai.features.communication.contacts.ContactIntelligence
import com.sona.ai.features.communication.email.EmailAssistant
import com.sona.ai.features.communication.messaging.MessagingAssistant
import com.sona.ai.features.communication.notifications.NotificationIntelligence
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CommunicationViewModel @Inject constructor(
    private val notificationIntelligence: NotificationIntelligence,
    private val messagingAssistant: MessagingAssistant,
    private val callingAssistant: CallingAssistant,
    private val emailAssistant: EmailAssistant,
    private val contactIntelligence: ContactIntelligence
) : ViewModel() {

    private val _state = MutableStateFlow(CommunicationState())
    val state: StateFlow<CommunicationState> = _state.asStateFlow()

    init {
        loadInitialState()
    }

    private fun loadInitialState() {
        viewModelScope.launch {
            _state.value = CommunicationState(
                unreadCount = notificationIntelligence.getUnreadCount(),
                messageCount = messagingAssistant.getConversationCount(),
                missedCalls = callingAssistant.getMissedCallCount(),
                unreadEmails = emailAssistant.getUnreadCount(),
                contactInsights = contactIntelligence.getInsightCount()
            )
        }
    }

    fun summarizeNotifications() {
        viewModelScope.launch {
            _state.value = _state.value.copy(summary = notificationIntelligence.generateSummary())
        }
    }

    fun summarizeMessages() {
        viewModelScope.launch {
            _state.value = _state.value.copy(summary = messagingAssistant.generateSummary())
        }
    }

    fun summarizeCalls() {
        viewModelScope.launch {
            _state.value = _state.value.copy(summary = callingAssistant.generateSummary())
        }
    }

    fun summarizeEmails() {
        viewModelScope.launch {
            _state.value = _state.value.copy(summary = emailAssistant.generateSummary())
        }
    }

    fun showContactInsights() {
        viewModelScope.launch {
            _state.value = _state.value.copy(summary = contactIntelligence.generateInsights())
        }
    }
}
