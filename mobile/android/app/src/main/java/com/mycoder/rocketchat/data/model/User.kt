package com.mycoder.rocketchat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.mycoder.rocketchat.data.local.Converters
import java.util.Date

/**
 * RocketChat user model
 */
@Entity(tableName = "users")
@TypeConverters(Converters::class)
data class User(
    @PrimaryKey
    val id: String,

    val username: String,
    val name: String?,
    val email: String?,

    // Profile
    val avatar: String? = null,
    val status: UserStatus = UserStatus.OFFLINE,
    val statusText: String? = null,
    val bio: String? = null,

    // Settings
    val timezone: String? = null,
    val language: String = "en",

    // Roles
    val roles: List<String> = emptyList(),

    // Timestamps
    val createdAt: Date,
    val lastLogin: Date? = null,

    // Current user flag
    val isCurrentUser: Boolean = false,

    // MyCoder preferences
    val preferredAiProvider: String? = null,
    val thermalMonitoring: Boolean = false
) {
    enum class UserStatus {
        ONLINE,
        AWAY,
        BUSY,
        OFFLINE
    }
}

/**
 * Authentication session
 */
data class AuthSession(
    val userId: String,
    val authToken: String,
    val serverUrl: String,
    val username: String,
    val expiresAt: Date? = null
)

/**
 * MyCoder API provider configuration
 */
data class ApiProviderConfig(
    val type: String,  // claude_anthropic, gemini, ollama_local, etc.
    val enabled: Boolean,
    val apiKey: String? = null,
    val baseUrl: String? = null,
    val timeout: Int = 30,
    val priority: Int = 0
)

/**
 * Thermal status for Q9550 integration
 */
data class ThermalStatus(
    val cpuTemp: Int,
    val status: String,  // normal, elevated, high, critical
    val safeOperation: Boolean,
    val timestamp: Long
)
