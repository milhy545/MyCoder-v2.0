package com.mycoder.rocketchat.data.repository

import com.mycoder.rocketchat.data.local.MyCoderDatabase
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.data.model.Room
import com.mycoder.rocketchat.data.model.User
import com.mycoder.rocketchat.network.MyCoderApiClient
import com.mycoder.rocketchat.network.RocketChatWebSocket
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.Date

/**
 * Central repository for chat data
 *
 * Implements offline-first architecture:
 * 1. Read from local database immediately
 * 2. Sync with server in background
 * 3. Update local database when server responds
 */
class ChatRepository private constructor(
    private val database: MyCoderDatabase,
    private val apiClient: MyCoderApiClient,
    private val webSocket: RocketChatWebSocket
) {
    private val repositoryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val messageDao = database.messageDao()
    private val roomDao = database.roomDao()
    private val userDao = database.userDao()

    init {
        // Listen to WebSocket messages
        repositoryScope.launch {
            webSocket.messages.collect { wsMessage ->
                handleWebSocketMessage(wsMessage)
            }
        }
    }

    // ========== Rooms ==========

    fun getAllRooms(): Flow<List<Room>> {
        return roomDao.getAllRooms()
    }

    fun getRoomById(roomId: String): Flow<Room?> {
        return roomDao.getRoomById(roomId)
    }

    fun getFavoriteRooms(): Flow<List<Room>> {
        return roomDao.getFavoriteRooms()
    }

    fun getUnreadRooms(): Flow<List<Room>> {
        return roomDao.getUnreadRooms()
    }

    suspend fun updateRoomFavorite(roomId: String, favorite: Boolean) {
        roomDao.updateFavorite(roomId, favorite)
    }

    suspend fun markRoomAsRead(roomId: String) {
        roomDao.updateUnreadCount(roomId, 0)
    }

    // ========== Messages ==========

    fun getMessagesForRoom(roomId: String, limit: Int = 50): Flow<List<Message>> {
        return messageDao.getMessagesForRoom(roomId, limit)
    }

    suspend fun sendMessage(roomId: String, message: String): Result<Message> {
        return try {
            // Create local message
            val user = userDao.getCurrentUserSync() ?: return Result.failure(Exception("Not logged in"))

            val localMessage = Message(
                id = "local_${System.currentTimeMillis()}",
                roomId = roomId,
                message = message,
                userId = user.id,
                username = user.username,
                timestamp = Date(),
                localOnly = true,
                sendingStatus = Message.SendingStatus.SENDING
            )

            // Save to database
            messageDao.insertMessage(localMessage)

            // Send via WebSocket
            webSocket.sendChatMessage(roomId, message)

            Result.success(localMessage)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendAIQuery(
        roomId: String,
        prompt: String,
        preferredProvider: String? = null
    ): Result<Message> {
        return try {
            val user = userDao.getCurrentUserSync() ?: return Result.failure(Exception("Not logged in"))

            // Create local message for user's query
            val queryMessage = Message(
                id = "local_${System.currentTimeMillis()}_query",
                roomId = roomId,
                message = prompt,
                userId = user.id,
                username = user.username,
                timestamp = Date(),
                localOnly = true,
                sendingStatus = Message.SendingStatus.SENDING
            )
            messageDao.insertMessage(queryMessage)

            // Query MyCoder API
            val response = apiClient.query(
                prompt = prompt,
                context = mapOf("roomId" to roomId),
                preferredProvider = preferredProvider
            )

            if (response.success) {
                // Create AI response message
                val aiMessage = Message(
                    id = "local_${System.currentTimeMillis()}_ai",
                    roomId = roomId,
                    message = response.content,
                    userId = "mycoder_ai",
                    username = "MyCoder AI",
                    timestamp = Date(),
                    isAiGenerated = true,
                    aiProvider = response.provider,
                    aiCost = response.cost,
                    aiTokens = response.tokensUsed,
                    localOnly = false,
                    sendingStatus = Message.SendingStatus.SENT
                )
                messageDao.insertMessage(aiMessage)

                // Update query message as sent
                messageDao.updateSendingStatus(queryMessage.id, Message.SendingStatus.SENT)

                Result.success(aiMessage)
            } else {
                // Mark query as failed
                messageDao.updateSendingStatus(queryMessage.id, Message.SendingStatus.FAILED)
                Result.failure(Exception(response.error ?: "AI query failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun toggleMessageStar(messageId: String, starred: Boolean) {
        messageDao.updateStarred(messageId, starred)
    }

    suspend fun searchMessages(roomId: String, query: String): List<Message> {
        return messageDao.searchMessages(roomId, query)
    }

    // ========== Users ==========

    fun getCurrentUser(): Flow<User?> {
        return userDao.getCurrentUser()
    }

    suspend fun setCurrentUser(user: User) {
        userDao.clearCurrentUser()
        userDao.insertUser(user.copy(isCurrentUser = true))
    }

    // ========== Sync ==========

    suspend fun syncWithServer() {
        // TODO: Implement server sync
        // This would fetch latest messages, rooms, etc. from RocketChat REST API
    }

    private suspend fun handleWebSocketMessage(wsMessage: RocketChatWebSocket.RocketChatMessage) {
        // Convert WebSocket message to local Message
        val message = Message(
            id = wsMessage.id,
            roomId = wsMessage.roomId,
            message = wsMessage.message,
            userId = wsMessage.userId,
            username = wsMessage.username,
            timestamp = Date(wsMessage.timestamp),
            synced = true,
            localOnly = false,
            sendingStatus = Message.SendingStatus.SENT
        )

        // Save to database
        messageDao.insertMessage(message)

        // Update room's last message time and increment unread
        val room = roomDao.getRoomByIdSync(wsMessage.roomId)
        if (room != null) {
            val currentUser = userDao.getCurrentUserSync()
            val isOwnMessage = wsMessage.userId == currentUser?.id

            roomDao.updateRoom(
                room.copy(
                    lastMessageAt = Date(wsMessage.timestamp),
                    unread = if (isOwnMessage) room.unread else room.unread + 1,
                    updatedAt = Date()
                )
            )
        }
    }

    companion object {
        @Volatile
        private var INSTANCE: ChatRepository? = null

        fun getInstance(
            database: MyCoderDatabase,
            apiClient: MyCoderApiClient,
            webSocket: RocketChatWebSocket
        ): ChatRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: ChatRepository(database, apiClient, webSocket).also {
                    INSTANCE = it
                }
            }
        }
    }
}
