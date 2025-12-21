package com.mycoder.rocketchat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.mycoder.rocketchat.data.local.Converters
import java.util.Date

/**
 * RocketChat message model
 * Compatible with both Room database and RocketChat REST/WebSocket API
 */
@Entity(tableName = "messages")
@TypeConverters(Converters::class)
data class Message(
    @PrimaryKey
    val id: String,

    val roomId: String,
    val message: String,
    val userId: String,
    val username: String,
    val timestamp: Date,

    // Optional fields
    val avatar: String? = null,
    val edited: Boolean = false,
    val editedAt: Date? = null,
    val attachments: List<Attachment>? = null,
    val mentions: List<Mention>? = null,
    val starred: Boolean = false,
    val pinned: Boolean = false,

    // AI-related fields (MyCoder integration)
    val isAiGenerated: Boolean = false,
    val aiProvider: String? = null,  // claude_anthropic, gemini, etc.
    val aiCost: Double? = null,
    val aiTokens: Int? = null,

    // Sync status
    val synced: Boolean = true,
    val localOnly: Boolean = false,
    val sendingStatus: SendingStatus = SendingStatus.SENT
) {
    enum class SendingStatus {
        PENDING,
        SENDING,
        SENT,
        FAILED
    }
}

/**
 * Message attachment (files, images, etc.)
 */
data class Attachment(
    val type: String,
    val title: String?,
    val description: String?,
    val url: String?,
    val imageUrl: String?,
    val thumbUrl: String?,
    val size: Long?,
    val mimeType: String?
)

/**
 * User mention in message
 */
data class Mention(
    val userId: String,
    val username: String,
    val name: String?
)

/**
 * Message reaction (emoji)
 */
data class Reaction(
    val emoji: String,
    val userIds: List<String>,
    val count: Int
)
