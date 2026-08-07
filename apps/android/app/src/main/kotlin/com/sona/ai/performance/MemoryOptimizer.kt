package com.sona.ai.performance

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MemoryOptimizer @Inject constructor() {

    fun trimMemory(level: Int) {
        if (level >= 60) clearCaches()
    }

    private fun clearCaches() {
        // Release non-critical cached data
    }

    fun getMemoryStats(): MemoryStats {
        val runtime = Runtime.getRuntime()
        return MemoryStats(
            totalMb = runtime.maxMemory() / 1024 / 1024,
            usedMb = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024,
            freeMb = runtime.freeMemory() / 1024 / 1024
        )
    }
}

data class MemoryStats(
    val totalMb: Long,
    val usedMb: Long,
    val freeMb: Long
)
