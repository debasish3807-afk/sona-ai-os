package com.sona.ai.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.sona.ai.data.local.entity.MemoryEntity
import kotlinx.coroutines.flow.Flow

/**
 * Room DAO for memory operations.
 * Provides methods for caching and querying memories locally.
 */
@Dao
interface MemoryDao {

    @Query("SELECT * FROM memories ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories ORDER BY timestamp DESC")
    suspend fun getAll(): List<MemoryEntity>

    @Query("SELECT * FROM memories WHERE category = :category ORDER BY timestamp DESC")
    suspend fun getByCategory(category: String): List<MemoryEntity>

    @Query("SELECT * FROM memories WHERE id = :id")
    suspend fun getById(id: String): MemoryEntity?

    @Query(
        "SELECT * FROM memories WHERE content LIKE '%' || :query || '%' " +
        "OR category LIKE '%' || :query || '%' " +
        "ORDER BY timestamp DESC"
    )
    suspend fun search(query: String): List<MemoryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(memory: MemoryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(memories: List<MemoryEntity>)

    @Update
    suspend fun update(memory: MemoryEntity)

    @Query("DELETE FROM memories WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM memories")
    suspend fun deleteAll()

    @Query("SELECT COUNT(*) FROM memories WHERE isSynced = 0")
    suspend fun getUnsyncedCount(): Int

    @Query("SELECT * FROM memories WHERE isSynced = 0")
    suspend fun getUnsynced(): List<MemoryEntity>

    @Query("UPDATE memories SET isSynced = 1 WHERE id = :id")
    suspend fun markSynced(id: String)
}
