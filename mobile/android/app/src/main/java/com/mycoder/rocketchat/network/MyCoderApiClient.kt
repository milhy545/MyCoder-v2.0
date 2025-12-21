package com.mycoder.rocketchat.network

import android.content.Context
import com.google.gson.Gson
import com.google.gson.GsonBuilder
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

    private var baseUrl: String = BuildConfig.MYCODER_API_URL
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

    fun setBaseUrl(url: String) {
        baseUrl = url
        isInitialized = false
    }

    companion object {
        private const val TAG = "MyCoderApiClient"

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
