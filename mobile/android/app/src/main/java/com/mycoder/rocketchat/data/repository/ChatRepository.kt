package com.mycoder.rocketchat.data.repository

import com.mycoder.rocketchat.data.local.MyCoderDatabase
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.data.model.Room
import com.mycoder.rocketchat.data.model.User
import com.mycoder.rocketchat.network.ChatSyncMessage
import com.mycoder.rocketchat.network.ChatSyncRoom
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
    private var lastSyncEpochMs: Long? = null

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

    /**
     * Synchronize local database with RocketChat server.
     * Fetches latest messages, room updates, and subscriptions.
     */
    suspend fun syncWithServer() {
        android.util.Log.d(TAG, "Syncing with RocketChat server...")
        try {
            val syncPayload = apiClient.fetchChatSync(lastSyncEpochMs)
            if (!syncPayload.success) {
                android.util.Log.w(TAG, "Sync request failed: ${syncPayload.error}")
                return
            }

            upsertRooms(syncPayload.rooms)
            upsertMessages(syncPayload.messages)

            lastSyncEpochMs = syncPayload.serverTime
                ?: syncPayload.messages.maxOfOrNull { it.timestamp }
                ?: System.currentTimeMillis()

            android.util.Log.d(
                TAG,
                "Sync complete. rooms=${syncPayload.rooms.size}, messages=${syncPayload.messages.size}, since=$lastSyncEpochMs"
            )
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to sync with server", e)
        }
    }

    private suspend fun upsertRooms(rooms: List<ChatSyncRoom>) {
        if (rooms.isEmpty()) return

        val mappedRooms = rooms.map { remoteRoom ->
            val existing = roomDao.getRoomByIdSync(remoteRoom.id)
            Room(
                id = remoteRoom.id,
                name = remoteRoom.name.ifBlank { existing?.name ?: remoteRoom.id },
                type = remoteRoom.type.toRoomTypeOrDefault(existing?.type),
                description = existing?.description,
                topic = existing?.topic,
                announcement = existing?.announcement,
                createdAt = existing?.createdAt ?: Date(),
                updatedAt = remoteRoom.updatedAt?.let(::Date) ?: Date(),
                lastMessageAt = remoteRoom.lastMessageAt?.let(::Date) ?: existing?.lastMessageAt,
                readonly = existing?.readonly ?: false,
                archived = remoteRoom.archived,
                favorite = remoteRoom.favorite,
                open = existing?.open ?: true,
                unread = remoteRoom.unread,
                mentions = existing?.mentions ?: 0,
                usernames = existing?.usernames ?: emptyList(),
                numberOfUsers = existing?.numberOfUsers ?: 0,
                aiEnabled = existing?.aiEnabled ?: true,
                preferredAiProvider = existing?.preferredAiProvider,
                thermalAware = existing?.thermalAware ?: true,
                synced = true
            )
        }

        roomDao.insertRooms(mappedRooms)
    }

    private suspend fun upsertMessages(messages: List<ChatSyncMessage>) {
        if (messages.isEmpty()) return

        val mappedMessages = messages.map { remoteMessage ->
            Message(
                id = remoteMessage.id,
                roomId = remoteMessage.roomId,
                message = remoteMessage.message,
                userId = remoteMessage.userId,
                username = remoteMessage.username,
                timestamp = Date(remoteMessage.timestamp),
                synced = remoteMessage.synced,
                localOnly = false,
                sendingStatus = Message.SendingStatus.SENT
            )
        }

        messageDao.insertMessages(mappedMessages)
    }

    private fun String?.toRoomTypeOrDefault(defaultType: Room.RoomType?): Room.RoomType {
        return when (this?.lowercase()) {
            "c", "channel" -> Room.RoomType.CHANNEL
            "p", "private", "private_group", "group" -> Room.RoomType.PRIVATE_GROUP
            "d", "dm", "direct", "direct_message" -> Room.RoomType.DIRECT_MESSAGE
            "l", "livechat" -> Room.RoomType.LIVECHAT
            else -> defaultType ?: Room.RoomType.CHANNEL
        }
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
        private const val TAG = "ChatRepository"

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
