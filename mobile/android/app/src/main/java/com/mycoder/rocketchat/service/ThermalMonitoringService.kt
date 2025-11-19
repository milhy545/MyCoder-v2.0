package com.mycoder.rocketchat.service

import android.content.Context
import android.os.Build
import android.os.PowerManager
import androidx.annotation.RequiresApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Thermal Monitoring Service
 *
 * Integrates with MyCoder v2.0 thermal awareness system
 * for Q9550 and modern Android devices
 */
class ThermalMonitoringService(private val context: Context) {

    private val _thermalState = MutableStateFlow(ThermalState.NOMINAL)
    val thermalState: Flow<ThermalState> = _thermalState.asStateFlow()

    private val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager

    /**
     * Check current thermal status
     */
    fun getCurrentThermalStatus(): ThermalStatus {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            getCurrentThermalStatusModern()
        } else {
            getCurrentThermalStatusLegacy()
        }
    }

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun getCurrentThermalStatusModern(): ThermalStatus {
        val thermalStatus = powerManager.currentThermalStatus

        val state = when (thermalStatus) {
            PowerManager.THERMAL_STATUS_NONE -> ThermalState.NOMINAL
            PowerManager.THERMAL_STATUS_LIGHT -> ThermalState.NOMINAL
            PowerManager.THERMAL_STATUS_MODERATE -> ThermalState.ELEVATED
            PowerManager.THERMAL_STATUS_SEVERE -> ThermalState.HIGH
            PowerManager.THERMAL_STATUS_CRITICAL -> ThermalState.CRITICAL
            PowerManager.THERMAL_STATUS_EMERGENCY -> ThermalState.CRITICAL
            PowerManager.THERMAL_STATUS_SHUTDOWN -> ThermalState.CRITICAL
            else -> ThermalState.NOMINAL
        }

        _thermalState.value = state

        return ThermalStatus(
            state = state,
            safeForHeavyOperations = state == ThermalState.NOMINAL || state == ThermalState.ELEVATED,
            timestamp = System.currentTimeMillis()
        )
    }

    private fun getCurrentThermalStatusLegacy(): ThermalStatus {
        // Legacy devices: assume nominal unless device is in power save mode
        val isPowerSaveMode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            powerManager.isPowerSaveMode
        } else {
            false
        }

        val state = if (isPowerSaveMode) ThermalState.ELEVATED else ThermalState.NOMINAL
        _thermalState.value = state

        return ThermalStatus(
            state = state,
            safeForHeavyOperations = !isPowerSaveMode,
            timestamp = System.currentTimeMillis()
        )
    }

    /**
     * Get recommended AI provider based on thermal state
     */
    fun getRecommendedProvider(): String? {
        return when (_thermalState.value) {
            ThermalState.NOMINAL -> null  // Auto-select
            ThermalState.ELEVATED -> "ollama_local"  // Prefer local
            ThermalState.HIGH -> "ollama_local"  // Force local
            ThermalState.CRITICAL -> null  // Consider blocking AI operations
        }
    }

    /**
     * Check if heavy AI operations are safe
     */
    fun isSafeForAI(): Boolean {
        return _thermalState.value != ThermalState.CRITICAL
    }

    enum class ThermalState {
        NOMINAL,    // Normal operation
        ELEVATED,   // Slightly warm, prefer local processing
        HIGH,       // Hot, use local only
        CRITICAL    // Critical temperature, avoid AI operations
    }

    data class ThermalStatus(
        val state: ThermalState,
        val safeForHeavyOperations: Boolean,
        val timestamp: Long
    )

    companion object {
        @Volatile
        private var INSTANCE: ThermalMonitoringService? = null

        fun getInstance(context: Context): ThermalMonitoringService {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: ThermalMonitoringService(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}
