package com.mycoder.rocketchat.ui.compose.components

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mycoder.rocketchat.MyCoderApplication
import com.mycoder.rocketchat.service.SpeechRecognitionService
import com.mycoder.rocketchat.service.TextToSpeechService

/**
 * Voice input button with permission handling
 */
@Composable
fun VoiceInputButton(
    onTextRecognized: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    val context = LocalContext.current
    val application = context.applicationContext as MyCoderApplication
    val speechRecognition = application.speechRecognition

    val listeningState by speechRecognition.listeningState.collectAsStateWithLifecycle()
    val partialResults by speechRecognition.partialResults.collectAsStateWithLifecycle()
    val finalResults by speechRecognition.finalResults.collectAsStateWithLifecycle()
    val error by speechRecognition.error.collectAsStateWithLifecycle()

    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasPermission = isGranted
        if (isGranted) {
            speechRecognition.startListening("cs-CZ")
        }
    }

    // Handle final results
    LaunchedEffect(finalResults) {
        finalResults?.let { result ->
            onTextRecognized(result.text)
        }
    }

    Column(modifier = modifier) {
        // Microphone button
        IconButton(
            onClick = {
                when (listeningState) {
                    SpeechRecognitionService.ListeningState.IDLE -> {
                        if (hasPermission) {
                            speechRecognition.startListening("cs-CZ")
                        } else {
                            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        }
                    }
                    SpeechRecognitionService.ListeningState.LISTENING -> {
                        speechRecognition.stopListening()
                    }
                    else -> {
                        speechRecognition.cancel()
                    }
                }
            },
            enabled = enabled
        ) {
            Box {
                // Animated pulsing effect when listening
                if (listeningState == SpeechRecognitionService.ListeningState.LISTENING) {
                    PulsingCircle()
                }

                Icon(
                    imageVector = when (listeningState) {
                        SpeechRecognitionService.ListeningState.LISTENING -> Icons.Default.MicOff
                        else -> Icons.Default.Mic
                    },
                    contentDescription = "Voice input",
                    tint = when (listeningState) {
                        SpeechRecognitionService.ListeningState.LISTENING -> MaterialTheme.colorScheme.primary
                        SpeechRecognitionService.ListeningState.ERROR -> MaterialTheme.colorScheme.error
                        else -> if (enabled) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurface.copy(
                            alpha = 0.38f
                        )
                    }
                )
            }
        }

        // Show partial results while listening
        AnimatedVisibility(visible = partialResults.isNotEmpty()) {
            Card(
                modifier = Modifier
                    .padding(horizontal = 8.dp)
                    .widthIn(max = 250.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Text(
                    text = partialResults,
                    modifier = Modifier.padding(8.dp),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
        }

        // Show error
        error?.let { errorMessage ->
            Snackbar(
                modifier = Modifier.padding(8.dp),
                action = {
                    TextButton(onClick = { speechRecognition.clearError() }) {
                        Text("OK")
                    }
                }
            ) {
                Text(errorMessage)
            }
        }
    }
}

/**
 * Text-to-Speech playback button
 */
@Composable
fun TextToSpeechButton(
    text: String,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    val context = LocalContext.current
    val application = context.applicationContext as MyCoderApplication
    val textToSpeech = application.textToSpeech

    val speakingState by textToSpeech.speakingState.collectAsStateWithLifecycle()
    val error by textToSpeech.error.collectAsStateWithLifecycle()

    IconButton(
        onClick = {
            when (speakingState) {
                TextToSpeechService.SpeakingState.IDLE -> {
                    if (text.isNotBlank()) {
                        textToSpeech.speak(text)
                    }
                }
                TextToSpeechService.SpeakingState.SPEAKING -> {
                    textToSpeech.stop()
                }
                else -> {
                    textToSpeech.stop()
                }
            }
        },
        enabled = enabled && text.isNotBlank(),
        modifier = modifier
    ) {
        Icon(
            imageVector = when (speakingState) {
                TextToSpeechService.SpeakingState.SPEAKING -> Icons.Default.VolumeOff
                else -> Icons.Default.VolumeUp
            },
            contentDescription = "Play audio",
            tint = when (speakingState) {
                TextToSpeechService.SpeakingState.SPEAKING -> MaterialTheme.colorScheme.primary
                TextToSpeechService.SpeakingState.ERROR -> MaterialTheme.colorScheme.error
                else -> if (enabled && text.isNotBlank()) {
                    MaterialTheme.colorScheme.onSurface
                } else {
                    MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
                }
            }
        )
    }

    // Show error
    error?.let { errorMessage ->
        Snackbar(
            modifier = Modifier.padding(8.dp),
            action = {
                TextButton(onClick = { textToSpeech.clearError() }) {
                    Text("OK")
                }
            }
        ) {
            Text(errorMessage)
        }
    }
}

/**
 * Pulsing circle animation for microphone
 */
@Composable
fun PulsingCircle() {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )

    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_alpha"
    )

    Box(
        modifier = Modifier
            .size(48.dp)
            .scale(scale)
            .background(
                color = MaterialTheme.colorScheme.primary.copy(alpha = alpha),
                shape = CircleShape
            )
    )
}
