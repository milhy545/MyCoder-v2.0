package com.mycoder.rocketchat.network

import android.content.Context
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.mycoder.rocketchat.BuildConfig
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.launch
import okhttp3.*
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * RocketChat WebSocket client for real-time messaging
 *
 * Implements the RocketChat Realtime API protocol
 * https://developer.rocket.chat/reference/api/realtime-api
 */
class RocketChatWebSocket private constructor(private val context: Context) {

    private val gson = Gson()
    private val messageIdCounter = AtomicInteger(0)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private var webSocket: WebSocket? = null
    private var isConnected = false
    private var serverUrl: String = BuildConfig.ROCKETCHAT_SERVER

    // Event flows
    private val _connectionState = MutableSharedFlow<ConnectionState>(replay = 1)
    val connectionState: SharedFlow<ConnectionState> = _connectionState

    private val _messages = MutableSharedFlow<RocketChatMessage>()
    val messages: SharedFlow<RocketChatMessage> = _messages

    private val _errors = MutableSharedFlow<String>()
    val errors: SharedFlow<String> = _errors

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)  // No timeout for WebSocket
        .writeTimeout(10, TimeUnit.SECONDS)
        .pingInterval(30, TimeUnit.SECONDS)
        .build()

    /**
     * Connect to RocketChat server
     */
    fun connect(url: String = serverUrl, token: String? = null) {
        if (isConnected) {
            android.util.Log.d(TAG, "Already connected")
            return
        }

        serverUrl = url

        val request = Request.Builder()
            .url(serverUrl)
            .build()

        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                android.util.Log.d(TAG, "WebSocket connected")
                isConnected = true
                scope.launch {
                    _connectionState.emit(ConnectionState.CONNECTED)
                }

                // Send connect message
                sendMessage(mapOf(
                    "msg" to "connect",
                    "version" to "1",
                    "support" to listOf("1")
                ))

                // Login if token provided
                token?.let { loginWithToken(it) }
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                android.util.Log.d(TAG, "WebSocket message: $text")
                handleMessage(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                android.util.Log.d(TAG, "WebSocket closing: $code $reason")
                isConnected = false
                scope.launch {
                    _connectionState.emit(ConnectionState.DISCONNECTING)
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                android.util.Log.d(TAG, "WebSocket closed: $code $reason")
                isConnected = false
                scope.launch {
                    _connectionState.emit(ConnectionState.DISCONNECTED)
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                android.util.Log.e(TAG, "WebSocket error", t)
                isConnected = false
                scope.launch {
                    _connectionState.emit(ConnectionState.ERROR)
                    _errors.emit(t.message ?: "Unknown error")
                }
            }
        })
    }

    /**
     * Disconnect from RocketChat server
     */
    fun disconnect() {
        webSocket?.close(1000, "Normal closure")
        webSocket = null
        isConnected = false
    }

    /**
     * Login with authentication token
     */
    fun loginWithToken(token: String) {
        sendMessage(mapOf(
            "msg" to "method",
            "method" to "login",
            "id" to nextId(),
            "params" to listOf(
                mapOf("resume" to token)
            )
        ))
    }

    /**
     * Subscribe to room messages
     */
    fun subscribeToRoom(roomId: String) {
        sendMessage(mapOf(
            "msg" to "sub",
            "id" to nextId(),
            "name" to "stream-room-messages",
            "params" to listOf(roomId, false)
        ))
    }

    /**
     * Send chat message
     */
    fun sendChatMessage(roomId: String, message: String) {
        sendMessage(mapOf(
            "msg" to "method",
            "method" to "sendMessage",
            "id" to nextId(),
            "params" to listOf(
                mapOf(
                    "rid" to roomId,
                    "msg" to message
                )
            )
        ))
    }

    /**
     * Send AI query through MyCoder
     */
    fun sendAIQuery(roomId: String, prompt: String, preferredProvider: String? = null) {
        sendMessage(mapOf(
            "msg" to "method",
            "method" to "mycoder.query",
            "id" to nextId(),
            "params" to listOf(
                mapOf(
                    "rid" to roomId,
                    "prompt" to prompt,
                    "preferred_provider" to preferredProvider
                )
            )
        ))
    }

    private fun sendMessage(data: Map<String, Any>) {
        val json = gson.toJson(data)
        android.util.Log.d(TAG, "Sending: $json")
        webSocket?.send(json)
    }

    private fun handleMessage(text: String) {
        try {
            val json = gson.fromJson(text, JsonObject::class.java)
            val msgType = json.get("msg")?.asString

            when (msgType) {
                "ping" -> {
                    // Respond to ping
                    sendMessage(mapOf("msg" to "pong"))
                }
                "connected" -> {
                    android.util.Log.d(TAG, "Session connected")
                }
                "result" -> {
                    // Method result
                    val id = json.get("id")?.asString
                    android.util.Log.d(TAG, "Result for $id")
                }
                "changed" -> {
                    // Data changed (new message, etc.)
                    val collection = json.get("collection")?.asString
                    if (collection == "stream-room-messages") {
                        val fields = json.getAsJsonObject("fields")
                        val args = fields.getAsJsonArray("args")
                        if (args != null && args.size() > 0) {
                            val messageJson = args[0].asJsonObject
                            val message = parseMessage(messageJson)
                            scope.launch {
                                _messages.emit(message)
                            }
                        }
                    }
                }
                "error" -> {
                    val error = json.get("reason")?.asString ?: "Unknown error"
                    android.util.Log.e(TAG, "Error: $error")
                    scope.launch {
                        _errors.emit(error)
                    }
                }
            }
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to parse message", e)
        }
    }

    private fun parseMessage(json: JsonObject): RocketChatMessage {
        return RocketChatMessage(
            id = json.get("_id")?.asString ?: "",
            roomId = json.get("rid")?.asString ?: "",
            message = json.get("msg")?.asString ?: "",
            userId = json.getAsJsonObject("u")?.get("_id")?.asString ?: "",
            username = json.getAsJsonObject("u")?.get("username")?.asString ?: "",
            timestamp = json.getAsJsonObject("ts")?.get("$date")?.asLong ?: System.currentTimeMillis()
        )
    }

    private fun nextId(): String {
        return messageIdCounter.incrementAndGet().toString()
    }

    enum class ConnectionState {
        DISCONNECTED,
        CONNECTING,
        CONNECTED,
        DISCONNECTING,
        ERROR
    }

    data class RocketChatMessage(
        val id: String,
        val roomId: String,
        val message: String,
        val userId: String,
        val username: String,
        val timestamp: Long
    )

    companion object {
        private const val TAG = "RocketChatWebSocket"

        @Volatile
        private var INSTANCE: RocketChatWebSocket? = null

        fun getInstance(context: Context): RocketChatWebSocket {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: RocketChatWebSocket(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}
