package com.mycoder.rocketchat.ui.compose.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mycoder.rocketchat.data.model.Room
import com.mycoder.rocketchat.ui.viewmodel.ChatViewModel
import java.text.SimpleDateFormat
import java.util.*

/**
 * Rooms list screen
 */
@Composable
fun RoomsScreen(
    viewModel: ChatViewModel,
    showFavorites: Boolean,
    modifier: Modifier = Modifier
) {
    val rooms by if (showFavorites) {
        viewModel.favoriteRooms.collectAsStateWithLifecycle()
    } else {
        viewModel.rooms.collectAsStateWithLifecycle()
    }

    Column(modifier = modifier.fillMaxSize()) {
        // Search bar
        SearchBar(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        )

        if (rooms.isEmpty()) {
            EmptyState(showFavorites = showFavorites)
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(vertical = 8.dp)
            ) {
                items(rooms, key = { it.id }) { room ->
                    RoomItem(
                        room = room,
                        onClick = { viewModel.selectRoom(room.id) },
                        onFavoriteClick = {
                            viewModel.toggleFavorite(room.id, !room.favorite)
                        }
                    )
                    Divider()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchBar(modifier: Modifier = Modifier) {
    var query by remember { mutableStateOf("") }

    OutlinedTextField(
        value = query,
        onValueChange = { query = it },
        modifier = modifier,
        placeholder = { Text("Search rooms...") },
        leadingIcon = { Icon(Icons.Default.Search, "Search") },
        singleLine = true,
        shape = MaterialTheme.shapes.extraLarge
    )
}

@Composable
fun RoomItem(
    room: Room,
    onClick: () -> Unit,
    onFavoriteClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val dateFormat = remember { SimpleDateFormat("HH:mm", Locale.getDefault()) }

    ListItem(
        modifier = modifier.clickable(onClick = onClick),
        headlineContent = {
            Text(
                text = room.name,
                fontWeight = if (room.unread > 0) FontWeight.Bold else FontWeight.Normal,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        },
        supportingContent = room.description?.let {
            {
                Text(
                    text = it,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        },
        leadingContent = {
            RoomIcon(room = room)
        },
        trailingContent = {
            Column(horizontalAlignment = Alignment.End) {
                room.lastMessageAt?.let {
                    Text(
                        text = dateFormat.format(it),
                        style = MaterialTheme.typography.labelSmall
                    )
                }
                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    if (room.unread > 0) {
                        Badge {
                            Text(room.unread.toString())
                        }
                    }
                    IconButton(onClick = onFavoriteClick) {
                        Icon(
                            imageVector = if (room.favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                            contentDescription = "Favorite",
                            tint = if (room.favorite) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    )
}

@Composable
fun RoomIcon(room: Room, modifier: Modifier = Modifier) {
    val icon = when (room.type) {
        Room.RoomType.CHANNEL -> Icons.Default.Tag
        Room.RoomType.PRIVATE_GROUP -> Icons.Default.Lock
        Room.RoomType.DIRECT_MESSAGE -> Icons.Default.Person
        Room.RoomType.LIVECHAT -> Icons.Default.Support
    }

    Icon(
        imageVector = icon,
        contentDescription = room.type.name,
        modifier = modifier.size(40.dp),
        tint = MaterialTheme.colorScheme.primary
    )
}

@Composable
fun EmptyState(showFavorites: Boolean, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = if (showFavorites) Icons.Default.FavoriteBorder else Icons.Default.ChatBubbleOutline,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = if (showFavorites) "No favorite rooms yet" else "No rooms found",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
