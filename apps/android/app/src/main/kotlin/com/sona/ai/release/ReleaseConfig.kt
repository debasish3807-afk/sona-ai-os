package com.sona.ai.release

object ReleaseConfig {
    const val VERSION_NAME = "0.1.0-beta"
    const val VERSION_CODE = 2
    const val BUILD_TYPE = "beta"
    const val PACKAGE_NAME = "com.sona.ai"
    const val MIN_SDK = 26
    const val TARGET_SDK = 35

    val RELEASE_NOTES = """
        Sona AI OS v0.1.0-beta
        
        First public beta release!
        
        Features:
        • AI Chat with streaming responses
        • Voice Assistant (continuous mode + wake word)
        • Vision AI (OCR, analysis, documents)
        • Memory System (short-term + long-term)
        • Multi-Agent Workforce
        • GitHub & Google integration
        • Daily Dashboard
        • Offline support
        
        Known limitations:
        • Requires Ollama for local AI inference
        • Some features require internet connection
        • Voice features require microphone permission
    """.trimIndent()

    val CHANGELOG = listOf(
        "0.1.0-beta" to "First public beta release with full AI pipeline",
        "0.1.0-alpha" to "Internal alpha with core services implemented"
    )
}
