package com.mycoder.rocketchat.ui

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.mycoder.rocketchat.BuildConfig
import com.mycoder.rocketchat.MyCoderApplication
import com.mycoder.rocketchat.R
import com.mycoder.rocketchat.databinding.ActivityMainBinding
import com.mycoder.rocketchat.ui.viewmodel.ChatViewModel
import kotlinx.coroutines.launch

/**
 * Main Activity
 *
 * Automatically selects UI implementation based on build variant:
 * - Modern (API 29+): Uses Jetpack Compose with Material Design 3
 * - Legacy (API 19+): Uses traditional XML layouts with AppCompat
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var viewModel: ChatViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize ViewModel
        val application = application as MyCoderApplication
        val factory = ChatViewModel.Factory(application.chatRepository)
        viewModel = ViewModelProvider(this, factory)[ChatViewModel::class.java]

        // Select UI based on build variant
        if (BuildConfig.SUPPORTS_MATERIAL3) {
            // Modern variant - use Compose
            initializeComposeUI()
        } else {
            // Legacy variant - use XML layouts
            initializeXmlUI()
        }

        // Initialize WebSocket connection
        initializeWebSocket()
    }

    private fun initializeComposeUI() {
        // Modern Compose UI will be set via setContent in modern source set
        // This is handled in modern/MainActivity.kt
    }

    private fun initializeXmlUI() {
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Setup toolbar
        setSupportActionBar(binding.toolbar)

        // Setup navigation (legacy)
        // This will be implemented in legacy/MainActivity.kt
    }

    private fun initializeWebSocket() {
        val application = application as MyCoderApplication

        lifecycleScope.launch {
            try {
                // Connect to WebSocket
                application.webSocket.connect(
                    url = BuildConfig.ROCKETCHAT_SERVER
                )
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Failed to connect WebSocket", e)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        // Disconnect WebSocket when activity is destroyed
        (application as? MyCoderApplication)?.webSocket?.disconnect()
    }

    companion object {
        private const val TAG = "MainActivity"
    }
}
