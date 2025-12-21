package com.mycoder.rocketchat.ui.compose

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mycoder.rocketchat.ui.compose.screens.ChatScreen
import com.mycoder.rocketchat.ui.compose.screens.RoomsScreen
import com.mycoder.rocketchat.ui.viewmodel.ChatViewModel

/**
 * Main Compose App
 * Modern Material Design 3 UI
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyCoderApp(
    viewModel: ChatViewModel,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableStateOf(0) }
    val currentRoomId by viewModel.currentRoomId.collectAsStateWithLifecycle()

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = { Text("MyCoder RocketChat") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                ),
                actions = {
                    IconButton(onClick = { /* Settings */ }) {
                        Icon(Icons.Default.Settings, "Settings")
                    }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Icon(Icons.Default.Chat, "Chats") },
                    label = { Text("Chats") }
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Icon(Icons.Default.Favorite, "Favorites") },
                    label = { Text("Favorites") }
                )
                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    icon = { Icon(Icons.Default.Person, "Profile") },
                    label = { Text("Profile") }
                )
            }
        }
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            when {
                currentRoomId != null -> {
                    ChatScreen(
                        viewModel = viewModel,
                        onBackPressed = { viewModel.selectRoom("") }
                    )
                }
                else -> {
                    when (selectedTab) {
                        0 -> RoomsScreen(
                            viewModel = viewModel,
                            showFavorites = false
                        )
                        1 -> RoomsScreen(
                            viewModel = viewModel,
                            showFavorites = true
                        )
                        2 -> ProfileScreen()
                    }
                }
            }
        }
    }
}

@Composable
fun ProfileScreen() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = androidx.compose.ui.Alignment.Center
    ) {
        Text("Profile Screen - Coming Soon")
    }
}
