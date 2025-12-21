package com.mycoder.rocketchat.service

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*

/**
 * Speech Recognition Service
 *
 * Provides Speech-to-Text functionality using Android's native SpeechRecognizer.
 * Compatible with Android 4.4+ (API 19+)
 *
 * Features:
 * - Offline speech recognition (device-dependent)
 * - Real-time partial results
 * - Multiple language support
 * - Error handling with user-friendly messages
 */
class SpeechRecognitionService(private val context: Context) {

    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false

    // State flows for UI
    private val _listeningState = MutableStateFlow(ListeningState.IDLE)
    val listeningState: StateFlow<ListeningState> = _listeningState.asStateFlow()

    private val _partialResults = MutableStateFlow("")
    val partialResults: StateFlow<String> = _partialResults.asStateFlow()

    private val _finalResults = MutableStateFlow<SpeechResult?>(null)
    val finalResults: StateFlow<SpeechResult?> = _finalResults.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    init {
        checkAvailability()
    }

    /**
     * Check if speech recognition is available on this device
     */
    fun isAvailable(): Boolean {
        return SpeechRecognizer.isRecognitionAvailable(context)
    }

    /**
     * Start listening for speech input
     */
    fun startListening(language: String = "cs-CZ") {
        if (isListening) {
            android.util.Log.w(TAG, "Already listening")
            return
        }

        if (!isAvailable()) {
            _error.value = "Speech recognition not available on this device"
            return
        }

        try {
            // Create speech recognizer if needed
            if (speechRecognizer == null) {
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
                speechRecognizer?.setRecognitionListener(recognitionListener)
            }

            // Create intent for speech recognition
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, language)
                putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
            }

            // Start listening
            _listeningState.value = ListeningState.LISTENING
            _partialResults.value = ""
            _error.value = null
            isListening = true

            speechRecognizer?.startListening(intent)
            android.util.Log.d(TAG, "Started listening for language: $language")

        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to start listening", e)
            _error.value = "Failed to start speech recognition: ${e.message}"
            _listeningState.value = ListeningState.ERROR
            isListening = false
        }
    }

    /**
     * Stop listening
     */
    fun stopListening() {
        if (!isListening) return

        try {
            speechRecognizer?.stopListening()
            isListening = false
            _listeningState.value = ListeningState.PROCESSING
            android.util.Log.d(TAG, "Stopped listening")
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to stop listening", e)
            _error.value = "Failed to stop: ${e.message}"
            _listeningState.value = ListeningState.ERROR
            isListening = false
        }
    }

    /**
     * Cancel listening
     */
    fun cancel() {
        if (!isListening) return

        try {
            speechRecognizer?.cancel()
            isListening = false
            _listeningState.value = ListeningState.IDLE
            _partialResults.value = ""
            android.util.Log.d(TAG, "Cancelled listening")
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to cancel", e)
            isListening = false
        }
    }

    /**
     * Reset error state
     */
    fun clearError() {
        _error.value = null
    }

    /**
     * Release resources
     */
    fun destroy() {
        try {
            speechRecognizer?.destroy()
            speechRecognizer = null
            isListening = false
            _listeningState.value = ListeningState.IDLE
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Error destroying speech recognizer", e)
        }
    }

    private fun checkAvailability() {
        if (!isAvailable()) {
            android.util.Log.w(TAG, "Speech recognition not available")
            _error.value = "Speech recognition is not available on this device"
        }
    }

    private val recognitionListener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            android.util.Log.d(TAG, "Ready for speech")
            _listeningState.value = ListeningState.LISTENING
        }

        override fun onBeginningOfSpeech() {
            android.util.Log.d(TAG, "Beginning of speech")
            _listeningState.value = ListeningState.LISTENING
        }

        override fun onRmsChanged(rmsdB: Float) {
            // Volume level changed - can be used for visual feedback
        }

        override fun onBufferReceived(buffer: ByteArray?) {
            // Audio buffer received
        }

        override fun onEndOfSpeech() {
            android.util.Log.d(TAG, "End of speech")
            _listeningState.value = ListeningState.PROCESSING
            isListening = false
        }

        override fun onError(error: Int) {
            val errorMessage = when (error) {
                SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
                SpeechRecognizer.ERROR_NETWORK -> "Network error"
                SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                SpeechRecognizer.ERROR_NO_MATCH -> "No speech match found"
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognition service busy"
                SpeechRecognizer.ERROR_SERVER -> "Server error"
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input"
                else -> "Unknown error: $error"
            }

            android.util.Log.e(TAG, "Speech recognition error: $errorMessage")
            _error.value = errorMessage
            _listeningState.value = ListeningState.ERROR
            isListening = false
        }

        override fun onResults(results: Bundle?) {
            android.util.Log.d(TAG, "Got final results")

            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            val confidence = results?.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)

            if (!matches.isNullOrEmpty()) {
                val result = SpeechResult(
                    text = matches[0],
                    alternatives = matches,
                    confidence = confidence?.getOrNull(0)
                )

                _finalResults.value = result
                _partialResults.value = ""
                android.util.Log.d(TAG, "Recognized: ${result.text}")
            }

            _listeningState.value = ListeningState.IDLE
            isListening = false
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if (!matches.isNullOrEmpty()) {
                _partialResults.value = matches[0]
                android.util.Log.d(TAG, "Partial: ${matches[0]}")
            }
        }

        override fun onEvent(eventType: Int, params: Bundle?) {
            // Reserved for future use
        }
    }

    enum class ListeningState {
        IDLE,           // Not listening
        LISTENING,      // Actively listening
        PROCESSING,     // Processing speech
        ERROR           // Error occurred
    }

    data class SpeechResult(
        val text: String,
        val alternatives: List<String>,
        val confidence: Float?
    )

    companion object {
        private const val TAG = "SpeechRecognitionService"

        @Volatile
        private var INSTANCE: SpeechRecognitionService? = null

        fun getInstance(context: Context): SpeechRecognitionService {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SpeechRecognitionService(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}
