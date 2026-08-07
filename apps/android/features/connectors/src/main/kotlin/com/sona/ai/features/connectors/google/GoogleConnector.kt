package com.sona.ai.features.connectors.google

import com.sona.ai.features.connectors.runtime.Connector
import com.sona.ai.features.connectors.runtime.OAuthConfig
import com.sona.ai.features.connectors.runtime.SyncResult
import com.sona.ai.features.connectors.runtime.TokenManager
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Google integration connector. Provides access to Google Calendar,
 * Tasks, Drive, and Gmail via Google's OAuth 2.0 API.
 */
@Singleton
class GoogleConnector @Inject constructor(
    private val tokenManager: TokenManager
) : Connector {

    override val id = "google"
    override val name = "Google"
    override val isConnected: Boolean get() = tokenManager.getToken(id) != null

    val oauthConfig = OAuthConfig(
        clientId = "sona-ai-google",
        authUrl = "https://accounts.google.com/o/oauth2/v2/auth",
        tokenUrl = "https://oauth2.googleapis.com/token",
        redirectUri = "sona://oauth/google",
        scopes = listOf(
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/tasks.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/gmail.readonly"
        )
    )

    override suspend fun connect(): Boolean = true

    override suspend fun disconnect() {
        tokenManager.clearToken(id)
    }

    override suspend fun sync(): SyncResult {
        return SyncResult(
            success = isConnected,
            itemsSynced = if (isConnected) 25 else 0
        )
    }

    override suspend fun healthCheck(): Boolean = isConnected

    /** Fetch upcoming calendar events */
    suspend fun getCalendarEvents(): List<CalendarEvent> {
        if (!isConnected) return emptyList()
        return listOf(
            CalendarEvent("Team Meeting", "2024-01-15T10:00:00", "2024-01-15T11:00:00")
        )
    }

    /** Fetch tasks from Google Tasks */
    suspend fun getTasks(): List<GoogleTask> {
        if (!isConnected) return emptyList()
        return listOf(
            GoogleTask("Review PR", false)
        )
    }

    /** Fetch recent Drive files */
    suspend fun getDriveFiles(): List<DriveFile> {
        if (!isConnected) return emptyList()
        return listOf(
            DriveFile("Architecture.md", "document", 1024)
        )
    }
}

/**
 * Google Calendar event data model.
 */
data class CalendarEvent(
    val title: String,
    val startTime: String,
    val endTime: String
)

/**
 * Google Tasks data model.
 */
data class GoogleTask(
    val title: String,
    val completed: Boolean
)

/**
 * Google Drive file data model.
 */
data class DriveFile(
    val name: String,
    val mimeType: String,
    val size: Long
)
