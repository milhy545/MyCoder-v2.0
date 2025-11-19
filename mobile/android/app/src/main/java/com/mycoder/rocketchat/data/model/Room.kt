package com.mycoder.rocketchat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.mycoder.rocketchat.data.local.Converters
import java.util.Date

/**
 * RocketChat room (channel, direct message, group)
 */
@Entity(tableName = "rooms")
@TypeConverters(Converters::class)
data class Room(
    @PrimaryKey
    val id: String,

    val name: String,
    val type: RoomType,
    val description: String? = null,
    val topic: String? = null,
    val announcement: String? = null,

    // Timestamps
    val createdAt: Date,
    val updatedAt: Date,
    val lastMessageAt: Date? = null,

    // Room settings
    val readonly: Boolean = false,
    val archived: Boolean = false,
    val favorite: Boolean = false,
    val open: Boolean = true,

    // Unread counts
    val unread: Int = 0,
    val mentions: Int = 0,

    // Users
    val usernames: List<String> = emptyList(),
    val numberOfUsers: Int = 0,

    // AI features (MyCoder integration)
    val aiEnabled: Boolean = true,
    val preferredAiProvider: String? = null,  // null = auto-select
    val thermalAware: Boolean = true,

    // Sync status
    val synced: Boolean = true
) {
    enum class RoomType {
        CHANNEL,        // Public channel (#)
        PRIVATE_GROUP,  // Private group
        DIRECT_MESSAGE, // 1-on-1 DM
        LIVECHAT       // Support chat
    }
}

/**
 * Room subscription (user's relationship with room)
 */
@Entity(tableName = "subscriptions")
data class Subscription(
    @PrimaryKey
    val id: String,

    val roomId: String,
    val userId: String,
    val name: String,
    val type: Room.RoomType,

    // Notification settings
    val alert: Boolean = true,
    val desktopNotifications: String = "all",
    val mobilePushNotifications: String = "all",
    val emailNotifications: String = "nothing",
    val audioNotifications: String = "all",

    // UI state
    val unread: Int = 0,
    val mentions: Int = 0,
    val open: Boolean = true,
    val hideUnreadStatus: Boolean = false,

    // Timestamps
    val lastSeen: Date? = null,
    val updatedAt: Date
)
