package com.sona.ai.navigation

/**
 * Sealed class representing navigation destinations in the app.
 */
sealed class Screen(val route: String) {

    data object Splash : Screen("splash")

    data object Login : Screen("login")

    data object Home : Screen("home")

    data object Chat : Screen("chat") {
        fun withConversationId(conversationId: String) = "chat/$conversationId"
        const val ROUTE_WITH_ARG = "chat/{conversationId}"
        const val ARG_CONVERSATION_ID = "conversationId"
    }

    data object Settings : Screen("settings")

    data object Memory : Screen("memory")
}
