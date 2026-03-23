package com.mycoder.rocketchat.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.mycoder.rocketchat.MyCoderApplication
import com.mycoder.rocketchat.R
import kotlinx.coroutines.*

/**
 * Background service for syncing messages
 */
class MessageSyncService : Service() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var syncJob: Job? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        ensureForegroundService()

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

    private fun ensureForegroundService() {
        createNotificationChannel()
        val notification = buildForegroundNotification()
        startForeground(NOTIFICATION_ID, notification)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return

        val notificationManager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            NOTIFICATION_CHANNEL_ID,
            "Message Sync",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Keeps chat messages in sync in the background"
            setShowBadge(false)
        }

        notificationManager.createNotificationChannel(channel)
    }

    private fun buildForegroundNotification(): Notification {
        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("MyCoder sync active")
            .setContentText("Synchronizing messages every 15 minutes")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    companion object {
        private const val TAG = "MessageSyncService"
        private const val SYNC_INTERVAL = 15 * 60 * 1000L // 15 minutes
        private const val NOTIFICATION_CHANNEL_ID = "message_sync"
        private const val NOTIFICATION_ID = 3101
    }
}
