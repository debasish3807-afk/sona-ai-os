package com.sona.ai.offline

import javax.inject.Inject
import javax.inject.Singleton

data class OfflineData(
    val cachedChats: Int,
    val cachedMemories: Int,
    val offlineTasks: Int,
    val offlineNotes: Int,
    val lastSyncTime: Long
)

@Singleton
class OfflineDashboard @Inject constructor() {

    private var _data = OfflineData(
        cachedChats = 0,
        cachedMemories = 0,
        offlineTasks = 0,
        offlineNotes = 0,
        lastSyncTime = 0
    )

    fun getData(): OfflineData = _data

    fun updateCacheStats(chats: Int, memories: Int, tasks: Int, notes: Int) {
        _data = OfflineData(chats, memories, tasks, notes, System.currentTimeMillis())
    }

    fun isOfflineCapable(): Boolean = _data.cachedChats > 0 || _data.offlineTasks > 0
}
