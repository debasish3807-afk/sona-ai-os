package com.sona.ai.features.communication.contacts

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

data class ContactProfile(
    val name: String,
    val relationship: String = "unknown",
    val lastInteraction: Long = 0,
    val interactionCount: Int = 0,
    val notes: List<String> = emptyList()
)

@Singleton
class ContactIntelligence @Inject constructor() {
    private val profiles = mutableMapOf<String, ContactProfile>()

    fun updateProfile(name: String, relationship: String = "unknown") {
        profiles[name] = profiles.getOrDefault(name, ContactProfile(name)).copy(
            relationship = relationship,
            interactionCount = (profiles[name]?.interactionCount ?: 0) + 1,
            lastInteraction = System.currentTimeMillis()
        )
    }

    fun getInsightCount(): Int = profiles.size

    fun getProfile(name: String): ContactProfile? = profiles[name]

    fun getFrequentContacts(limit: Int = 5): List<ContactProfile> =
        profiles.values.sortedByDescending { it.interactionCount }.take(limit)

    fun generateInsights(): String {
        if (profiles.isEmpty()) return "No contact insights yet. Interact with contacts to build relationship memory."
        val top = getFrequentContacts(3)
        return "Top contacts: ${top.joinToString { "${it.name} (${it.interactionCount} interactions)" }}. Total tracked: ${profiles.size}."
    }

    fun getInteractionTimeline(name: String): String =
        profiles[name]?.let {
            val dateFormat = SimpleDateFormat("MMM dd", Locale.US)
            "Last interaction: ${dateFormat.format(Date(it.lastInteraction))}. Total: ${it.interactionCount} interactions."
        } ?: "No interaction history."
}
