package com.mycoder.rocketchat.network

import android.content.Context
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.mycoder.rocketchat.BuildConfig
import com.mycoder.rocketchat.data.model.ApiProviderConfig
import com.mycoder.rocketchat.data.model.ThermalStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import java.util.concurrent.TimeUnit

/**
 * MyCoder v2.0 API Client
 *
 * Integrates with the 5-tier API provider system:
 * 1. Claude Anthropic API
 * 2. Claude OAuth
 * 3. Gemini
 * 4. Ollama Local
 * 5. Ollama Remote
 */
class MyCoderApiClient private constructor(private val context: Context) {

    private val gson: Gson = GsonBuilder()
        .setLenient()
        .create()

    private val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        })
        .build()

    private var baseUrl: String = normalizeUrlProtocol(BuildConfig.MYCODER_API_URL)
    private var isInitialized = false

    suspend fun initialize() {
        if (isInitialized) return

        withContext(Dispatchers.IO) {
            try {
                // Test connection to MyCoder backend
                val request = Request.Builder()
                    .url("$baseUrl/health")
                    .get()
                    .build()

                val response = okHttpClient.newCall(request).execute()
                isInitialized = response.isSuccessful
                response.close()
            } catch (e: Exception) {
                android.util.Log.w(TAG, "Failed to connect to MyCoder API: ${e.message}")
                // Continue anyway - offline mode
                isInitialized = true
            }
        }
    }

    /**
     * Query AI with automatic provider selection
     */
    suspend fun query(
        prompt: String,
        context: Map<String, Any>? = null,
        preferredProvider: String? = null
    ): ApiResponse {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = mapOf(
                    "prompt" to prompt,
                    "context" to context,
                    "preferred_provider" to preferredProvider
                )

                val json = gson.toJson(requestBody)
                val request = Request.Builder()
                    .url("$baseUrl/api/v2/query")
                    .post(json.toRequestBody("application/json".toMediaType()))
                    .build()

                val response = okHttpClient.newCall(request).execute()
                val responseBody = response.body?.string() ?: ""

                if (response.isSuccessful) {
                    val apiResponse = gson.fromJson(responseBody, ApiResponse::class.java)
                    response.close()
                    apiResponse
                } else {
                    response.close()
                    ApiResponse(
                        success = false,
                        content = "",
                        provider = "none",
                        error = "HTTP ${response.code}: ${response.message}"
                    )
                }
            } catch (e: Exception) {
                ApiResponse(
                    success = false,
                    content = "",
                    provider = "none",
                    error = "Network error: ${e.message}"
                )
            }
        }
    }

    /**
     * Get system status including thermal monitoring
     */
    suspend fun getSystemStatus(): SystemStatus? {
        return withContext(Dispatchers.IO) {
            try {
                val request = Request.Builder()
                    .url("$baseUrl/api/v2/status")
                    .get()
                    .build()

                val response = okHttpClient.newCall(request).execute()
                val responseBody = response.body?.string()

                if (response.isSuccessful && responseBody != null) {
                    val status = gson.fromJson(responseBody, SystemStatus::class.java)
                    response.close()
                    status
                } else {
                    response.close()
                    null
                }
            } catch (e: Exception) {
                android.util.Log.w(TAG, "Failed to get system status: ${e.message}")
                null
            }
        }
    }

    /**
     * Get available API providers
     */
    suspend fun getProviders(): List<ApiProviderConfig> {
        return withContext(Dispatchers.IO) {
            try {
                val request = Request.Builder()
                    .url("$baseUrl/api/v2/providers")
                    .get()
                    .build()

                val response = okHttpClient.newCall(request).execute()
                val responseBody = response.body?.string()

                if (response.isSuccessful && responseBody != null) {
                    val providersResponse = gson.fromJson(responseBody, ProvidersResponse::class.java)
                    response.close()
                    providersResponse.providers
                } else {
                    response.close()
                    emptyList()
                }
            } catch (e: Exception) {
                android.util.Log.w(TAG, "Failed to get providers: ${e.message}")
                emptyList()
            }
        }
    }

    /**
     * Fetch incremental chat sync payload from backend.
     */
    suspend fun fetchChatSync(sinceEpochMs: Long?): ChatSyncPayload {
        return withContext(Dispatchers.IO) {
            try {
                val requestUrl = buildString {
                    append("$baseUrl/api/v2/chat/sync")
                    sinceEpochMs?.let {
                        append("?since=")
                        append(it)
                    }
                }

                val request = Request.Builder()
                    .url(requestUrl)
                    .get()
                    .build()

                val response = okHttpClient.newCall(request).execute()
                val responseBody = response.body?.string() ?: ""

                if (!response.isSuccessful) {
                    val error = "HTTP ${response.code}: ${response.message}"
                    response.close()
                    return@withContext ChatSyncPayload(
                        success = false,
                        error = error
                    )
                }

                val payload = parseChatSyncPayload(responseBody)
                response.close()
                payload
            } catch (e: Exception) {
                ChatSyncPayload(
                    success = false,
                    error = "Network error: ${e.message}"
                )
            }
        }
    }

    private fun parseChatSyncPayload(responseBody: String): ChatSyncPayload {
        val root = gson.fromJson(responseBody, JsonObject::class.java)

        val roomsArray = root.getAsJsonArray("rooms") ?: JsonArray()
        val messagesArray = root.getAsJsonArray("messages") ?: JsonArray()

        return ChatSyncPayload(
            success = root.get("success")?.asBoolean ?: true,
            rooms = roomsArray.mapNotNull { element ->
                element.asJsonObject?.let { roomJson ->
                    ChatSyncRoom(
                        id = roomJson.get("id")?.asString ?: roomJson.get("_id")?.asString ?: return@let null,
                        name = roomJson.get("name")?.asString ?: roomJson.get("fname")?.asString ?: "",
                        type = roomJson.get("type")?.asString ?: roomJson.get("t")?.asString,
                        unread = roomJson.get("unread")?.asInt ?: 0,
                        favorite = roomJson.get("favorite")?.asBoolean ?: false,
                        archived = roomJson.get("archived")?.asBoolean ?: false,
                        lastMessageAt = roomJson.get("lastMessageAt")?.asLong,
                        updatedAt = roomJson.get("updatedAt")?.asLong
                    )
                }
            },
            messages = messagesArray.mapNotNull { element ->
                element.asJsonObject?.let { messageJson ->
                    ChatSyncMessage(
                        id = messageJson.get("id")?.asString ?: messageJson.get("_id")?.asString ?: return@let null,
                        roomId = messageJson.get("roomId")?.asString ?: messageJson.get("rid")?.asString ?: return@let null,
                        message = messageJson.get("message")?.asString ?: messageJson.get("msg")?.asString ?: "",
                        userId = messageJson.get("userId")?.asString
                            ?: messageJson.getAsJsonObject("u")?.get("_id")?.asString
                            ?: "",
                        username = messageJson.get("username")?.asString
                            ?: messageJson.getAsJsonObject("u")?.get("username")?.asString
                            ?: "unknown",
                        timestamp = messageJson.get("timestamp")?.asLong
                            ?: messageJson.getAsJsonObject("ts")?.get("$date")?.asLong
                            ?: System.currentTimeMillis(),
                        synced = messageJson.get("synced")?.asBoolean ?: true
                    )
                }
            },
            serverTime = root.get("serverTime")?.asLong,
            error = root.get("error")?.asString
        )
    }

    /**
     * Connect to the specified URL and verify health.
     * Returns Success(Unit) if successful, or Failure(Exception) with error details.
     */
    suspend fun connect(url: String): Result<Unit> {
        return withContext(Dispatchers.IO) {
            try {
                // Ensure URL has protocol
                val targetUrl = if (!url.startsWith("http")) "http://$url" else url
                baseUrl = targetUrl

                // Test connection to MyCoder backend /health
                val request = Request.Builder()
                    .url("$baseUrl/health")
                    .get()
                    .build()

                // Use a short timeout for the connection check if possible,
                // but we reuse the shared client which has 30s timeout.
                // We could create a new call.
                val response = okHttpClient.newCall(request).execute()

                if (response.isSuccessful) {
                    isInitialized = true
                    response.close()
                    Result.success(Unit)
                } else {
                    val message = "HTTP ${response.code}: ${response.message}"
                    response.close()
                    Result.failure(Exception(message))
                }
            } catch (e: Exception) {
                isInitialized = false
                Result.failure(e)
            }
        }
    }

    fun setBaseUrl(url: String) {
        baseUrl = normalizeUrlProtocol(url)
        isInitialized = false
    }

    companion object {
        private const val TAG = "MyCoderApiClient"

        /**
         * Normalizes URL protocol to ensure HTTPS is used by default.
         * HTTP is only allowed in DEBUG mode for development/testing purposes.
         *
         * @param url The URL to normalize
         * @return URL with appropriate protocol (HTTPS in production, HTTP allowed in DEBUG)
         */
        private fun normalizeUrlProtocol(url: String): String {
            val trimmedUrl = url.trim()

            return when {
                // URL already has HTTPS - keep it as is
                trimmedUrl.startsWith("https://", ignoreCase = true) -> trimmedUrl

                // URL has HTTP protocol
                trimmedUrl.startsWith("http://", ignoreCase = true) -> {
                    if (BuildConfig.DEBUG) {
                        // Allow HTTP in DEBUG mode for local development
                        android.util.Log.d(TAG, "Using HTTP protocol in DEBUG mode: $trimmedUrl")
                        trimmedUrl
                    } else {
                        // Force HTTPS in production/release builds
                        val httpsUrl = trimmedUrl.replaceFirst("http://", "https://", ignoreCase = true)
                        android.util.Log.w(TAG, "HTTP not allowed in production. Converted to HTTPS: $httpsUrl")
                        httpsUrl
                    }
                }

                // No protocol specified - default to HTTPS
                else -> {
                    val httpsUrl = "https://$trimmedUrl"
                    android.util.Log.d(TAG, "No protocol specified. Defaulting to HTTPS: $httpsUrl")
                    httpsUrl
                }
            }
        }

        @Volatile
        private var INSTANCE: MyCoderApiClient? = null

        fun getInstance(context: Context): MyCoderApiClient {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: MyCoderApiClient(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}

/**
 * API response model
 */
data class ApiResponse(
    val success: Boolean,
    val content: String,
    val provider: String,
    val sessionId: String? = null,
    val cost: Double? = null,
    val durationMs: Long? = null,
    val tokensUsed: Int? = null,
    val error: String? = null,
    val metadata: Map<String, Any>? = null
)

/**
 * System status response
 */
data class SystemStatus(
    val status: String,
    val workingDirectory: String,
    val activeSessions: Int,
    val providers: Map<String, ProviderHealth>,
    val thermal: ThermalStatus?,
    val mode: String
)

/**
 * Provider health
 */
data class ProviderHealth(
    val status: String,
    val available: Boolean,
    val lastCheck: Long?,
    val errorRate: Double?
)

/**
 * Providers response
 */
data class ProvidersResponse(
    val providers: List<ApiProviderConfig>
)

data class ChatSyncPayload(
    val success: Boolean,
    val rooms: List<ChatSyncRoom> = emptyList(),
    val messages: List<ChatSyncMessage> = emptyList(),
    val serverTime: Long? = null,
    val error: String? = null
)

data class ChatSyncRoom(
    val id: String,
    val name: String,
    val type: String? = null,
    val unread: Int = 0,
    val favorite: Boolean = false,
    val archived: Boolean = false,
    val lastMessageAt: Long? = null,
    val updatedAt: Long? = null
)

data class ChatSyncMessage(
    val id: String,
    val roomId: String,
    val message: String,
    val userId: String,
    val username: String,
    val timestamp: Long,
    val synced: Boolean = true
)
