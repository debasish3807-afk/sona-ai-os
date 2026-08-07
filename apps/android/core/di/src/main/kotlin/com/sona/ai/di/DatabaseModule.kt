package com.sona.ai.di

import android.content.Context
import androidx.room.Room
import com.sona.ai.data.local.SonaDatabase
import com.sona.ai.data.local.dao.ConversationDao
import com.sona.ai.data.local.dao.MessageDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module providing database-related dependencies.
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideSonaDatabase(
        @ApplicationContext context: Context
    ): SonaDatabase {
        return Room.databaseBuilder(
            context,
            SonaDatabase::class.java,
            SonaDatabase.DATABASE_NAME
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    @Singleton
    fun provideMessageDao(database: SonaDatabase): MessageDao {
        return database.messageDao()
    }

    @Provides
    @Singleton
    fun provideConversationDao(database: SonaDatabase): ConversationDao {
        return database.conversationDao()
    }
}
