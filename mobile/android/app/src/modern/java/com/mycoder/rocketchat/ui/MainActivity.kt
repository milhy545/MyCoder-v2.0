package com.mycoder.rocketchat.ui

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModelProvider
import com.mycoder.rocketchat.MyCoderApplication
import com.mycoder.rocketchat.ui.compose.MyCoderApp
import com.mycoder.rocketchat.ui.compose.theme.MyCoderTheme
import com.mycoder.rocketchat.ui.viewmodel.ChatViewModel

/**
 * Main Activity - Modern variant (Jetpack Compose)
 *
 * Uses Material Design 3 with Jetpack Compose
 * Minimum SDK: Android 10 (API 29)
 */
class MainActivity : androidx.appcompat.app.AppCompatActivity() {

    private lateinit var viewModel: ChatViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize ViewModel
        val application = application as MyCoderApplication
        val factory = ChatViewModel.Factory(application.chatRepository)
        viewModel = ViewModelProvider(this, factory)[ChatViewModel::class.java]

        // Set Compose UI
        setContent {
            MyCoderTheme {
                MyCoderApp(viewModel = viewModel)
            }
        }

        // Initialize WebSocket
        initializeWebSocket()
    }

    private fun initializeWebSocket() {
        val application = application as MyCoderApplication
        application.webSocket.connect()
    }

    override fun onDestroy() {
        super.onDestroy()
        (application as? MyCoderApplication)?.webSocket?.disconnect()
    }
}
