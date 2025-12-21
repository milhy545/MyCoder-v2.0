package com.mycoder.rocketchat.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.mycoder.rocketchat.data.local.dao.MessageDao
import com.mycoder.rocketchat.data.local.dao.RoomDao
import com.mycoder.rocketchat.data.local.dao.SubscriptionDao
import com.mycoder.rocketchat.data.local.dao.UserDao
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.data.model.Room
import com.mycoder.rocketchat.data.model.Subscription
import com.mycoder.rocketchat.data.model.User

/**
 * MyCoder RocketChat local database
 *
 * Offline-first architecture with Room persistence
 * Compatible with both modern and legacy Android versions
 */
@Database(
    entities = [
        Message::class,
        Room::class,
        Subscription::class,
        User::class
    ],
    version = 1,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class MyCoderDatabase : RoomDatabase() {

    abstract fun messageDao(): MessageDao
    abstract fun roomDao(): RoomDao
    abstract fun subscriptionDao(): SubscriptionDao
    abstract fun userDao(): UserDao

    companion object {
        private const val DATABASE_NAME = "mycoder_rocketchat.db"

        @Volatile
        private var INSTANCE: MyCoderDatabase? = null

        fun getInstance(context: Context): MyCoderDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: buildDatabase(context).also { INSTANCE = it }
            }
        }

        private fun buildDatabase(context: Context): MyCoderDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                MyCoderDatabase::class.java,
                DATABASE_NAME
            )
                .fallbackToDestructiveMigration()  // For development
                .addCallback(object : Callback() {
                    override fun onCreate(db: SupportSQLiteDatabase) {
                        super.onCreate(db)
                        // Database created
                    }

                    override fun onOpen(db: SupportSQLiteDatabase) {
                        super.onOpen(db)
                        // Database opened
                    }
                })
                .build()
        }

        // Future migrations
        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                // Add migration logic when needed
            }
        }
    }
}
