package com.mycoder.rocketchat.data.local.dao

import androidx.room.*
import com.mycoder.rocketchat.data.model.Message
import kotlinx.coroutines.flow.Flow

/**
 * Message Data Access Object
 */
@Dao
interface MessageDao {

    @Query("SELECT * FROM messages WHERE roomId = :roomId ORDER BY timestamp DESC LIMIT :limit")
    fun getMessagesForRoom(roomId: String, limit: Int = 50): Flow<List<Message>>

    @Query("SELECT * FROM messages WHERE roomId = :roomId ORDER BY timestamp DESC LIMIT :limit OFFSET :offset")
    suspend fun getMessagesForRoomPaged(roomId: String, limit: Int, offset: Int): List<Message>

    @Query("SELECT * FROM messages WHERE id = :messageId")
    suspend fun getMessageById(messageId: String): Message?

    @Query("SELECT * FROM messages WHERE localOnly = 1 AND sendingStatus != 'SENT'")
    suspend fun getUnsentMessages(): List<Message>

    @Query("SELECT * FROM messages WHERE roomId = :roomId AND message LIKE '%' || :searchQuery || '%' ORDER BY timestamp DESC")
    suspend fun searchMessages(roomId: String, searchQuery: String): List<Message>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: Message)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessages(messages: List<Message>)

    @Update
    suspend fun updateMessage(message: Message)

    @Delete
    suspend fun deleteMessage(message: Message)

    @Query("DELETE FROM messages WHERE roomId = :roomId")
    suspend fun deleteMessagesForRoom(roomId: String)

    @Query("DELETE FROM messages WHERE timestamp < :olderThan AND starred = 0")
    suspend fun deleteOldMessages(olderThan: Long)

    @Query("UPDATE messages SET starred = :starred WHERE id = :messageId")
    suspend fun updateStarred(messageId: String, starred: Boolean)

    @Query("UPDATE messages SET sendingStatus = :status WHERE id = :messageId")
    suspend fun updateSendingStatus(messageId: String, status: Message.SendingStatus)

    @Query("SELECT COUNT(*) FROM messages WHERE roomId = :roomId")
    suspend fun getMessageCount(roomId: String): Int
}
