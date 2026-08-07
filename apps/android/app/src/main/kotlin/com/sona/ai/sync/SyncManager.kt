package com.sona.ai.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Manages background synchronization using WorkManager.
 * Handles periodic sync, connectivity-triggered sync, and manual sync.
 */
@Singleton
class SyncManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    companion object {
        const val PERIODIC_SYNC_WORK = "sona_periodic_sync"
        const val ONE_TIME_SYNC_WORK = "sona_one_time_sync"
        private const val SYNC_INTERVAL_MINUTES = 15L
    }

    /**
     * Schedules periodic background sync.
     * Runs every 15 minutes when network is available.
     */
    fun schedulePeriodicSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
            SYNC_INTERVAL_MINUTES, TimeUnit.MINUTES
        )
            .setConstraints(constraints)
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                1, TimeUnit.MINUTES
            )
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            PERIODIC_SYNC_WORK,
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )
    }

    /**
     * Triggers an immediate one-time sync.
     * Used when the app comes back online or user manually triggers sync.
     */
    fun triggerImmediateSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(context).enqueue(syncRequest)
    }

    /**
     * Cancels all scheduled sync work.
     */
    fun cancelAllSync() {
        WorkManager.getInstance(context).cancelUniqueWork(PERIODIC_SYNC_WORK)
    }

    /**
     * Checks if sync is currently running.
     */
    fun isSyncRunning(): Boolean {
        val workInfos = WorkManager.getInstance(context)
            .getWorkInfosForUniqueWork(PERIODIC_SYNC_WORK)
            .get()
        return workInfos.any { it.state == androidx.work.WorkInfo.State.RUNNING }
    }
}
