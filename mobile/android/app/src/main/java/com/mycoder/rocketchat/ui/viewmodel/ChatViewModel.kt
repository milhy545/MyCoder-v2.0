package com.mycoder.rocketchat.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.mycoder.rocketchat.data.model.Message
import com.mycoder.rocketchat.data.model.Room
import com.mycoder.rocketchat.data.repository.ChatRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * ViewModel for chat functionality
 * Compatible with both modern (Compose) and legacy (XML) UIs
 */
class ChatViewModel(
    private val repository: ChatRepository
) : ViewModel() {

    // UI State
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    // Current room
    private val _currentRoomId = MutableStateFlow<String?>(null)
    val currentRoomId: StateFlow<String?> = _currentRoomId.asStateFlow()

    // Rooms list
    val rooms: StateFlow<List<Room>> = repository.getAllRooms()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    val favoriteRooms: StateFlow<List<Room>> = repository.getFavoriteRooms()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    val unreadRooms: StateFlow<List<Room>> = repository.getUnreadRooms()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    // Messages for current room
    val messages: StateFlow<List<Message>> = _currentRoomId
        .filterNotNull()
        .flatMapLatest { roomId ->
            repository.getMessagesForRoom(roomId, limit = 100)
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    // Current room details
    val currentRoom: StateFlow<Room?> = _currentRoomId
        .filterNotNull()
        .flatMapLatest { roomId ->
            repository.getRoomById(roomId)
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )

    fun selectRoom(roomId: String) {
        _currentRoomId.value = roomId
        viewModelScope.launch {
            repository.markRoomAsRead(roomId)
        }
    }

    fun sendMessage(message: String) {
        val roomId = _currentRoomId.value ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSending = true) }

            val result = repository.sendMessage(roomId, message)

            _uiState.update {
                it.copy(
                    isSending = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun sendAIQuery(prompt: String, preferredProvider: String? = null) {
        val roomId = _currentRoomId.value ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSending = true, isAiProcessing = true) }

            val result = repository.sendAIQuery(roomId, prompt, preferredProvider)

            _uiState.update {
                it.copy(
                    isSending = false,
                    isAiProcessing = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun toggleFavorite(roomId: String, favorite: Boolean) {
        viewModelScope.launch {
            repository.updateRoomFavorite(roomId, favorite)
        }
    }

    fun toggleMessageStar(messageId: String, starred: Boolean) {
        viewModelScope.launch {
            repository.toggleMessageStar(messageId, starred)
        }
    }

    fun searchMessages(query: String) {
        val roomId = _currentRoomId.value ?: return

        viewModelScope.launch {
            val results = repository.searchMessages(roomId, query)
            _uiState.update { it.copy(searchResults = results) }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    data class ChatUiState(
        val isSending: Boolean = false,
        val isAiProcessing: Boolean = false,
        val error: String? = null,
        val searchResults: List<Message> = emptyList()
    )

    class Factory(private val repository: ChatRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(ChatViewModel::class.java)) {
                return ChatViewModel(repository) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
