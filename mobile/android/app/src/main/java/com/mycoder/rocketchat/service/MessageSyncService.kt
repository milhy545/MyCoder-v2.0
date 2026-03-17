package com.mycoder.rocketchat.service

import android.app.Service
import android.content.Intent
import android.os.IBinder
import com.mycoder.rocketchat.MyCoderApplication
import kotlinx.coroutines.*

/**
 * Background service for syncing messages
 */
class MessageSyncService : Service() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var syncJob: Job? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (syncJob == null) {
            syncJob = serviceScope.launch {
                while (isActive) {
                    try {
                        syncMessages()
                    } catch (e: Exception) {
                        android.util.Log.e(TAG, "Error during background sync", e)
                    }
                    delay(SYNC_INTERVAL)
                }
            }
        }
        return START_STICKY
    }

    private suspend fun syncMessages() {
        val app = application as MyCoderApplication
        app.chatRepository.syncWithServer()
        android.util.Log.d(TAG, "Syncing messages in background")
    }

    override fun onDestroy() {
        syncJob?.cancel()
        serviceScope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "MessageSyncService"
        private const val SYNC_INTERVAL = 15 * 60 * 1000L // 15 minutes
    }
}
