package com.mycoder.rocketchat.service

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*

/**
 * Text-to-Speech Service
 *
 * Provides Text-to-Speech functionality using Android's native TTS engine.
 * Compatible with Android 4.4+ (API 19+)
 *
 * Features:
 * - Multiple language support (Czech, English, etc.)
 * - Speech rate control
 * - Pitch control
 * - Queue management for multiple messages
 * - Speaking state monitoring
 */
class TextToSpeechService(private val context: Context) {

    private var tts: TextToSpeech? = null
    private var isInitialized = false

    // State flows for UI
    private val _speakingState = MutableStateFlow(SpeakingState.IDLE)
    val speakingState: StateFlow<SpeakingState> = _speakingState.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    // Default settings
    var speechRate: Float = 1.0f
        set(value) {
            field = value.coerceIn(0.5f, 2.0f)
            tts?.setSpeechRate(field)
        }

    var pitch: Float = 1.0f
        set(value) {
            field = value.coerceIn(0.5f, 2.0f)
            tts?.setPitch(field)
        }

    var language: Locale = Locale("cs", "CZ")
        set(value) {
            field = value
            setLanguage(value)
        }

    init {
        initializeTTS()
    }

    private fun initializeTTS() {
        try {
            tts = TextToSpeech(context) { status ->
                if (status == TextToSpeech.SUCCESS) {
                    isInitialized = true
                    android.util.Log.d(TAG, "TTS initialized successfully")

                    // Set default language
                    setLanguage(language)

                    // Set default rate and pitch
                    tts?.setSpeechRate(speechRate)
                    tts?.setPitch(pitch)

                    // Set utterance progress listener
                    tts?.setOnUtteranceProgressListener(utteranceProgressListener)

                } else {
                    android.util.Log.e(TAG, "TTS initialization failed with status: $status")
                    _error.value = "Text-to-Speech initialization failed"
                    isInitialized = false
                }
            }
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error initializing TTS", e)
            _error.value = "Failed to initialize TTS: ${e.message}"
            isInitialized = false
        }
    }

    private fun setLanguage(locale: Locale) {
        if (!isInitialized) return

        val result = tts?.setLanguage(locale)
        when (result) {
            TextToSpeech.LANG_MISSING_DATA -> {
                android.util.Log.w(TAG, "Language data missing for ${locale.displayLanguage}")
                _error.value = "Language data missing for ${locale.displayLanguage}"
            }
            TextToSpeech.LANG_NOT_SUPPORTED -> {
                android.util.Log.w(TAG, "Language not supported: ${locale.displayLanguage}")
                _error.value = "Language not supported: ${locale.displayLanguage}"
            }
            else -> {
                android.util.Log.d(TAG, "Language set to: ${locale.displayLanguage}")
            }
        }
    }

    /**
     * Speak text immediately (clears queue)
     */
    fun speak(text: String, utteranceId: String = "msg_${System.currentTimeMillis()}") {
        if (!isInitialized) {
            _error.value = "TTS not initialized"
            return
        }

        if (text.isBlank()) {
            android.util.Log.w(TAG, "Cannot speak empty text")
            return
        }

        try {
            val params = Bundle().apply {
                putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
            }

            @Suppress("DEPRECATION")
            val result = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
                tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, utteranceId)
            } else {
                val paramsMap = hashMapOf(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID to utteranceId)
                tts?.speak(text, TextToSpeech.QUEUE_FLUSH, paramsMap)
            }

            if (result == TextToSpeech.SUCCESS) {
                _speakingState.value = SpeakingState.SPEAKING
                android.util.Log.d(TAG, "Started speaking: ${text.take(50)}...")
            } else {
                _error.value = "Failed to speak text"
            }
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error speaking text", e)
            _error.value = "Error: ${e.message}"
        }
    }

    /**
     * Add text to queue (doesn't interrupt current speech)
     */
    fun speakQueued(text: String, utteranceId: String = "msg_${System.currentTimeMillis()}") {
        if (!isInitialized) {
            _error.value = "TTS not initialized"
            return
        }

        if (text.isBlank()) return

        try {
            val params = Bundle().apply {
                putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
            }

            @Suppress("DEPRECATION")
            val result = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
                tts?.speak(text, TextToSpeech.QUEUE_ADD, params, utteranceId)
            } else {
                val paramsMap = hashMapOf(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID to utteranceId)
                tts?.speak(text, TextToSpeech.QUEUE_ADD, paramsMap)
            }

            if (result == TextToSpeech.SUCCESS) {
                android.util.Log.d(TAG, "Added to queue: ${text.take(50)}...")
            }
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error adding to queue", e)
            _error.value = "Error: ${e.message}"
        }
    }

    /**
     * Stop speaking immediately
     */
    fun stop() {
        if (!isInitialized) return

        try {
            tts?.stop()
            _speakingState.value = SpeakingState.IDLE
            android.util.Log.d(TAG, "Stopped speaking")
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error stopping TTS", e)
        }
    }

    /**
     * Check if currently speaking
     */
    fun isSpeaking(): Boolean {
        return tts?.isSpeaking ?: false
    }

    /**
     * Get available languages
     */
    fun getAvailableLanguages(): Set<Locale> {
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
            tts?.availableLanguages ?: emptySet()
        } else {
            // Fallback for older Android versions
            setOf(Locale.US, Locale("cs", "CZ"), Locale.UK)
        }
    }

    /**
     * Clear error state
     */
    fun clearError() {
        _error.value = null
    }

    /**
     * Release resources
     */
    fun shutdown() {
        try {
            tts?.stop()
            tts?.shutdown()
            tts = null
            isInitialized = false
            _speakingState.value = SpeakingState.IDLE
            android.util.Log.d(TAG, "TTS shut down")
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error shutting down TTS", e)
        }
    }

    private val utteranceProgressListener = object : UtteranceProgressListener() {
        override fun onStart(utteranceId: String?) {
            android.util.Log.d(TAG, "Started utterance: $utteranceId")
            _speakingState.value = SpeakingState.SPEAKING
        }

        override fun onDone(utteranceId: String?) {
            android.util.Log.d(TAG, "Completed utterance: $utteranceId")
            _speakingState.value = SpeakingState.IDLE
        }

        @Deprecated("Deprecated in Java")
        override fun onError(utteranceId: String?) {
            android.util.Log.e(TAG, "Error in utterance: $utteranceId")
            _error.value = "Speech error"
            _speakingState.value = SpeakingState.ERROR
        }

        override fun onError(utteranceId: String?, errorCode: Int) {
            android.util.Log.e(TAG, "Error in utterance $utteranceId: code $errorCode")
            _error.value = "Speech error: $errorCode"
            _speakingState.value = SpeakingState.ERROR
        }
    }

    enum class SpeakingState {
        IDLE,       // Not speaking
        SPEAKING,   // Currently speaking
        ERROR       // Error occurred
    }

    companion object {
        private const val TAG = "TextToSpeechService"

        @Volatile
        private var INSTANCE: TextToSpeechService? = null

        fun getInstance(context: Context): TextToSpeechService {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: TextToSpeechService(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}
