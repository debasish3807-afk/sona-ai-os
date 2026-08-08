package com.sona.ai.data.remote

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import javax.inject.Inject
import okhttp3.MediaType.Companion.toMediaType
import javax.inject.Singleton

/**
 * SSE (Server-Sent Events) streaming client for real-time AI responses.
 * Uses OkHttp's SSE support for streaming token-by-token responses.
 */
@Singleton
class SseClient @Inject constructor(
    private val okHttpClient: OkHttpClient
) {

    /**
     * Opens an SSE connection and emits streamed data tokens.
     *
     * @param url The SSE endpoint URL.
     * @param body The request body (JSON string).
     * @param token The auth bearer token.
     * @return A Flow emitting each streamed data token.
     */
    fun stream(url: String, body: String, token: String): Flow<String> = callbackFlow {
        val requestBody = okhttp3.RequestBody.create(
            "application/json".toMediaType(),
            body
        )

        val request = Request.Builder()
            .url(url)
            .post(requestBody)
            .header("Authorization", "Bearer $token")
            .header("Accept", "text/event-stream")
            .build()

        val listener = object : EventSourceListener() {
            override fun onEvent(
                eventSource: EventSource,
                id: String?,
                type: String?,
                data: String
            ) {
                if (data == "[DONE]") {
                    close()
                    return
                }
                trySend(data)
            }

            override fun onFailure(
                eventSource: EventSource,
                t: Throwable?,
                response: Response?
            ) {
                close(t ?: Exception("SSE connection failed"))
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }
        }

        val factory = EventSources.createFactory(okHttpClient)
        val eventSource = factory.newEventSource(request, listener)

        awaitClose {
            eventSource.cancel()
        }
    }
}
