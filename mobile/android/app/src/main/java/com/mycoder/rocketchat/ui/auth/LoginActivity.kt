package com.mycoder.rocketchat.ui.auth

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.mycoder.rocketchat.databinding.ActivityLoginBinding
import com.mycoder.rocketchat.network.MyCoderApiClient
import kotlinx.coroutines.launch

/**
 * Login Activity
 * Implements Cyberpunk/Terminal style auth for MyCoder v2.0
 */
class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val prefs by lazy { getSharedPreferences("mycoder_prefs", Context.MODE_PRIVATE) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Setup ViewBinding
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
    }

    private fun setupUI() {
        // Load last saved URL
        val lastUrl = prefs.getString("server_url", "")
        if (!lastUrl.isNullOrEmpty()) {
            binding.serverUrlInput.setText(lastUrl)
        }

        binding.connectButton.setOnClickListener {
            val url = binding.serverUrlInput.text.toString().trim()
            if (url.isEmpty()) {
                showError("URL cannot be empty")
                return@setOnClickListener
            }

            performConnect(url)
        }
    }

    private fun performConnect(url: String) {
        // Reset error state
        binding.errorText.visibility = View.INVISIBLE
        binding.connectButton.isEnabled = false
        binding.connectButton.text = "CONNECTING..."

        lifecycleScope.launch {
            // Use the API Client abstraction to connect
            val result = MyCoderApiClient.getInstance(this@LoginActivity).connect(url)

            result.fold(
                onSuccess = {
                    onConnectionSuccess(url)
                },
                onFailure = { error ->
                    showError(error.message ?: "Unknown Connection Error")
                }
            )

            binding.connectButton.isEnabled = true
            binding.connectButton.text = "CONNECT"
        }
    }

    private fun onConnectionSuccess(url: String) {
        // Save to prefs
        prefs.edit().putString("server_url", url).apply()

        // Navigate to MainActivity
        val intent = Intent(this, com.mycoder.rocketchat.ui.MainActivity::class.java)
        startActivity(intent)
        finish()
    }

    private fun showError(message: String) {
        binding.errorText.text = "> ERROR: $message"
        binding.errorText.visibility = View.VISIBLE
    }
}
