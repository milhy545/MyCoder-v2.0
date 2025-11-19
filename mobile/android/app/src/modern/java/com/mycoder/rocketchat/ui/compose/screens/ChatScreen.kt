package com.mycoder.rocketchat.ui.compose.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.ui.compose.components.TextToSpeechButton
import com.mycoder.rocketchat.ui.compose.components.VoiceInputButton
import com.mycoder.rocketchat.ui.viewmodel.ChatViewModel
import java.text.SimpleDateFormat
import java.util.*

/**
 * Chat screen with messages
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,
    onBackPressed: () -> Unit,
    modifier: Modifier = Modifier
) {
    val messages by viewModel.messages.collectAsStateWithLifecycle()
    val currentRoom by viewModel.currentRoom.collectAsStateWithLifecycle()
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    var messageText by remember { mutableStateOf("") }
    var showAiDialog by remember { mutableStateOf(false) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = { Text(currentRoom?.name ?: "Chat") },
                navigationIcon = {
                    IconButton(onClick = onBackPressed) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { /* Room info */ }) {
                        Icon(Icons.Default.Info, "Info")
                    }
                }
            )
        },
        bottomBar = {
            MessageInput(
                text = messageText,
                onTextChange = { messageText = it },
                onSend = {
                    if (messageText.isNotBlank()) {
                        viewModel.sendMessage(messageText)
                        messageText = ""
                    }
                },
                onAiClick = { showAiDialog = true },
                isSending = uiState.isSending
            )
        }
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            MessagesList(
                messages = messages,
                onStarClick = { message ->
                    viewModel.toggleMessageStar(message.id, !message.starred)
                }
            )

            if (uiState.isAiProcessing) {
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.TopCenter)
                )
            }
        }
    }

    if (showAiDialog) {
        AiQueryDialog(
            onDismiss = { showAiDialog = false },
            onQuery = { prompt, provider ->
                viewModel.sendAIQuery(prompt, provider)
                showAiDialog = false
            }
        )
    }
}

@Composable
fun MessagesList(
    messages: List<Message>,
    onStarClick: (Message) -> Unit,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        state = listState,
        reverseLayout = true,
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(messages.reversed(), key = { it.id }) { message ->
            MessageItem(
                message = message,
                onStarClick = { onStarClick(message) }
            )
        }
    }
}

@Composable
fun MessageItem(
    message: Message,
    onStarClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val dateFormat = remember { SimpleDateFormat("HH:mm", Locale.getDefault()) }

    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isAiGenerated) Arrangement.Start else Arrangement.End
    ) {
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = if (message.isAiGenerated) {
                MaterialTheme.colorScheme.secondaryContainer
            } else {
                MaterialTheme.colorScheme.primaryContainer
            },
            modifier = Modifier.widthIn(max = 300.dp)
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = message.username,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = if (message.isAiGenerated) {
                            MaterialTheme.colorScheme.secondary
                        } else {
                            MaterialTheme.colorScheme.primary
                        }
                    )
                    if (message.isAiGenerated) {
                        message.aiProvider?.let { provider ->
                            AssistChip(
                                onClick = { },
                                label = { Text(provider, style = MaterialTheme.typography.labelSmall) },
                                leadingIcon = {
                                    Icon(
                                        Icons.Default.SmartToy,
                                        "AI",
                                        modifier = Modifier.size(12.dp)
                                    )
                                },
                                modifier = Modifier.height(20.dp)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = message.message,
                    style = MaterialTheme.typography.bodyMedium
                )

                Spacer(modifier = Modifier.height(4.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = dateFormat.format(message.timestamp),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        if (message.aiCost != null) {
                            Text(
                                text = "$${String.format("%.4f", message.aiCost)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                        }

                        // Text-to-Speech button for AI messages
                        if (message.isAiGenerated) {
                            TextToSpeechButton(
                                text = message.message,
                                modifier = Modifier.size(20.dp)
                            )
                        }

                        IconButton(onClick = onStarClick, modifier = Modifier.size(20.dp)) {
                            Icon(
                                imageVector = if (message.starred) Icons.Default.Star else Icons.Default.StarBorder,
                                contentDescription = "Star",
                                modifier = Modifier.size(16.dp),
                                tint = if (message.starred) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun MessageInput(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: () -> Unit,
    onAiClick: () -> Unit,
    isSending: Boolean,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        tonalElevation = 3.dp
    ) {
        Row(
            modifier = Modifier
                .padding(8.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            // Voice input button
            VoiceInputButton(
                onTextRecognized = onTextChange,
                enabled = !isSending
            )

            // AI Query button
            IconButton(onClick = onAiClick) {
                Icon(
                    Icons.Default.SmartToy,
                    "AI Query",
                    tint = MaterialTheme.colorScheme.primary
                )
            }

            // Text input
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Message or speak...") },
                maxLines = 4,
                enabled = !isSending
            )

            // Send button
            IconButton(
                onClick = onSend,
                enabled = text.isNotBlank() && !isSending
            ) {
                Icon(
                    Icons.Default.Send,
                    "Send",
                    tint = if (text.isNotBlank() && !isSending) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )
            }
        }
    }
}

@Composable
fun AiQueryDialog(
    onDismiss: () -> Unit,
    onQuery: (String, String?) -> Unit
) {
    var prompt by remember { mutableStateOf("") }
    var selectedProvider by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("AI Query") },
        text = {
            Column {
                OutlinedTextField(
                    value = prompt,
                    onValueChange = { prompt = it },
                    label = { Text("Prompt") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 5
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text("Provider (optional):", style = MaterialTheme.typography.labelSmall)
                // Provider selection would go here
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onQuery(prompt, selectedProvider) },
                enabled = prompt.isNotBlank()
            ) {
                Text("Send")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
