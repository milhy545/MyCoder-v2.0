# MyCoder RocketChat - Mobile Architecture

## Overview

The MyCoder RocketChat mobile app implements a production-ready Android application with dual API level support, integrating RocketChat messaging with MyCoder v2.1.0's 5-tier AI provider system.

## Dual Build System

### Modern Variant (Android 10+, API 29+)
**Technology Stack:**
- **UI**: Jetpack Compose with Material Design 3
- **Minimum SDK**: 29 (Android 10)
- **Target SDK**: 34 (Android 14)
- **Features**:
  - Modern Material Design 3 components
  - Compose-based declarative UI
  - Advanced thermal monitoring via PowerManager API
  - Biometric authentication support
  - Dynamic color theming

**Target Devices:**
- Modern smartphones (2019+)
- Tablets with Android 10+
- Optimized for performance on newer hardware

### Legacy Variant (Android 4.4+, API 19+)
**Technology Stack:**
- **UI**: Traditional XML layouts with AppCompat
- **Minimum SDK**: 19 (Android 4.4 KitKat)
- **Target SDK**: 34 (Android 14)
- **Features**:
  - AppCompat for Material Design backports
  - Fragment-based navigation
  - MultiDex support for method count limits
  - Java 8+ desugaring for modern APIs
  - Fallback thermal monitoring via power save mode

**Target Devices:**
- Older smartphones (2013-2019)
- Budget Android devices
- Legacy tablets (e.g., Android 4.4 tablets as mentioned by user)
- Embedded Android devices

## Architecture Pattern: MVVM

```
┌─────────────────────────────────────────────────────┐
│                      View Layer                      │
│  ┌────────────────────┐   ┌────────────────────────┐│
│  │ Jetpack Compose    │   │ XML + Fragments        ││
│  │ (Modern)           │   │ (Legacy)               ││
│  │ - Material 3       │   │ - AppCompat            ││
│  │ - Compose UI       │   │ - RecyclerView         ││
│  └────────────────────┘   └────────────────────────┘│
└──────────────────┬──────────────────────────────────┘
                   │ StateFlow
┌──────────────────▼──────────────────────────────────┐
│                  ViewModel Layer                     │
│  ┌──────────────────────────────────────────────┐   │
│  │ ChatViewModel                                │   │
│  │ - UI State Management                        │   │
│  │ - Business Logic                             │   │
│  │ - Lifecycle Awareness                        │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │ Repository Pattern
┌──────────────────▼──────────────────────────────────┐
│                  Repository Layer                    │
│  ┌──────────────────────────────────────────────┐   │
│  │ ChatRepository                               │   │
│  │ - Offline-first data management              │   │
│  │ - Data synchronization                       │   │
│  │ - WebSocket message handling                 │   │
│  └──────────────────────────────────────────────┘   │
└──────────────┬──────────────────┬──────────────────┘
               │                  │
    ┌──────────▼────────┐  ┌─────▼─────────┐
    │  Local Database   │  │ Network Layer │
    │  (Room)           │  │ (Retrofit +   │
    │  - Messages       │  │  WebSocket)   │
    │  - Rooms          │  │               │
    │  - Users          │  └───────────────┘
    │  - Subscriptions  │
    └───────────────────┘
```

## Data Flow

### Offline-First Architecture

```
User Action
    ↓
ViewModel receives event
    ↓
Repository checks local cache
    ↓
┌───────────────┬───────────────┐
│ Cache HIT     │ Cache MISS    │
│   ↓           │   ↓           │
│ Return data   │ Fetch from    │
│ immediately   │ network       │
│               │   ↓           │
│               │ Update cache  │
│               │   ↓           │
│               │ Return data   │
└───────────────┴───────────────┘
    ↓
Update UI via StateFlow
```

### Real-time Updates (WebSocket)

```
RocketChat Server
    ↓ WebSocket
RocketChatWebSocket
    ↓ SharedFlow
ChatRepository
    ↓ Room Database
    ↓ StateFlow
ViewModel
    ↓ StateFlow
UI (Compose/Fragments)
```

## Key Components

### 1. Application Layer

**MyCoderApplication.kt**
```kotlin
class MyCoderApplication : Application() {
    // Singletons
    val database: MyCoderDatabase
    val apiClient: MyCoderApiClient
    val webSocket: RocketChatWebSocket
    val chatRepository: ChatRepository

    // Initialization
    - MultiDex support
    - Database preloading
    - API client setup
    - Thermal monitoring (if supported)
}
```

### 2. Data Layer

#### Room Database
```kotlin
@Database(entities = [Message, Room, Subscription, User])
abstract class MyCoderDatabase : RoomDatabase {
    abstract fun messageDao(): MessageDao
    abstract fun roomDao(): RoomDao
    abstract fun subscriptionDao(): SubscriptionDao
    abstract fun userDao(): UserDao
}
```

**Entities:**
- `Message`: Chat messages with AI metadata (provider, cost, tokens)
- `Room`: Chat rooms/channels
- `Subscription`: User's room subscriptions
- `User`: User information

#### Network Layer

**MyCoderApiClient.kt** - MyCoder v2.1.0 Integration
```kotlin
class MyCoderApiClient {
    suspend fun query(
        prompt: String,
        context: Map<String, Any>?,
        preferredProvider: String?
    ): ApiResponse

    suspend fun getSystemStatus(): SystemStatus?
    suspend fun getProviders(): List<ApiProviderConfig>
}
```

**RocketChatWebSocket.kt** - Real-time Messaging
```kotlin
class RocketChatWebSocket {
    fun connect(url: String, token: String?)
    fun disconnect()
    fun sendMessage(roomId: String, message: String)
    fun sendAIQuery(roomId: String, prompt: String, provider: String?)
    fun subscribeToRoom(roomId: String)

    val messages: SharedFlow<RocketChatMessage>
    val connectionState: SharedFlow<ConnectionState>
}
```

### 3. Repository Pattern

**ChatRepository.kt**
```kotlin
class ChatRepository {
    // Rooms
    fun getAllRooms(): Flow<List<Room>>
    fun getRoomById(roomId: String): Flow<Room?>

    // Messages
    fun getMessagesForRoom(roomId: String): Flow<List<Message>>
    suspend fun sendMessage(roomId: String, message: String): Result<Message>
    suspend fun sendAIQuery(
        roomId: String,
        prompt: String,
        preferredProvider: String?
    ): Result<Message>

    // Sync
    suspend fun syncWithServer()
}
```

### 4. ViewModel Layer

**ChatViewModel.kt**
```kotlin
class ChatViewModel(repository: ChatRepository) : ViewModel() {
    // State
    val uiState: StateFlow<ChatUiState>
    val rooms: StateFlow<List<Room>>
    val messages: StateFlow<List<Message>>
    val currentRoom: StateFlow<Room?>

    // Actions
    fun selectRoom(roomId: String)
    fun sendMessage(message: String)
    fun sendAIQuery(prompt: String, preferredProvider: String?)
    fun toggleFavorite(roomId: String, favorite: Boolean)
}
```

### 5. UI Layer

#### Modern Variant (Jetpack Compose)

**MyCoderApp.kt** - Main Compose scaffold
```kotlin
@Composable
fun MyCoderApp(viewModel: ChatViewModel) {
    Scaffold(
        topBar = { TopAppBar(...) },
        bottomBar = { NavigationBar(...) }
    ) {
        // Navigation between screens
        when (currentScreen) {
            is Rooms -> RoomsScreen(viewModel)
            is Chat -> ChatScreen(viewModel)
        }
    }
}
```

**Screens:**
- `RoomsScreen`: List of chat rooms
- `ChatScreen`: Chat interface with messages
- `ProfileScreen`: User profile (placeholder)

#### Legacy Variant (XML + Fragments)

**Activity + Fragments:**
- `MainActivity`: Container activity with bottom navigation
- `RoomsFragment`: RecyclerView of rooms
- `ChatFragment`: RecyclerView of messages with input
- `ProfileFragment`: User profile (placeholder)

**Adapters:**
- `RoomsAdapter`: Binds Room data to views
- `MessagesAdapter`: Binds Message data to views

## MyCoder v2.1.0 Integration

### AI Provider System

The app integrates with MyCoder's 5-tier provider system:

1. **Claude Anthropic API** (Priority 1)
2. **Claude OAuth** (Priority 2)
3. **Gemini** (Priority 3)
4. **Ollama Local** (Priority 4)
5. **Ollama Remote** (Priority 5)

### Thermal-Aware Provider Selection

```kotlin
class ThermalMonitoringService {
    fun getCurrentThermalStatus(): ThermalStatus
    fun getRecommendedProvider(): String?
    fun isSafeForAI(): Boolean

    enum class ThermalState {
        NOMINAL     // → Auto-select provider
        ELEVATED    // → Prefer Ollama Local
        HIGH        // → Force Ollama Local
        CRITICAL    // → Block AI operations
    }
}
```

**Modern (Android 10+):**
```kotlin
val thermalStatus = powerManager.currentThermalStatus
when (thermalStatus) {
    THERMAL_STATUS_NONE -> "Auto-select"
    THERMAL_STATUS_MODERATE -> "ollama_local"
    THERMAL_STATUS_SEVERE -> "ollama_local"
    THERMAL_STATUS_CRITICAL -> null // Block
}
```

**Legacy (Android 4.4+):**
```kotlin
val isPowerSaveMode = powerManager.isPowerSaveMode
if (isPowerSaveMode) "ollama_local" else "Auto-select"
```

### AI Message Metadata

Messages from AI include:
```kotlin
data class Message(
    ...
    val isAiGenerated: Boolean,
    val aiProvider: String?,      // e.g., "claude_anthropic"
    val aiCost: Double?,           // e.g., 0.0023
    val aiTokens: Int?             // e.g., 150
)
```

## Background Services

### 1. ThermalMonitoringService
- Monitors device temperature
- Recommends AI provider based on thermal state
- Compatible with modern and legacy devices

### 2. MessageSyncService
- Background sync of messages
- Handles offline message queue
- Retries failed sends

### 3. MyCoderMessagingService
- Push notifications (placeholder for FCM)
- Handles incoming message notifications

## Build System

### Gradle Configuration

**Product Flavors:**
```kotlin
flavorDimensions += "apiLevel"

productFlavors {
    create("modern") {
        dimension = "apiLevel"
        minSdk = 29
        buildConfigField("boolean", "SUPPORTS_MATERIAL3", "true")
    }

    create("legacy") {
        dimension = "apiLevel"
        minSdk = 19
        buildConfigField("boolean", "SUPPORTS_MATERIAL3", "false")
    }
}
```

**Source Sets:**
```
src/
├── main/           # Shared code (90%)
├── modern/         # Modern-specific (Compose UI)
└── legacy/         # Legacy-specific (Fragment UI)
```

### Dependencies Management

**Shared Dependencies:**
- AndroidX Core, AppCompat
- Room, Lifecycle, Navigation
- Retrofit, OkHttp, WebSocket
- Kotlin Coroutines, Flow

**Modern-Only:**
- Jetpack Compose
- Material 3
- Compose Navigation
- Biometric API

**Legacy-Only:**
- MultiDex
- Desugar libs
- RecyclerView

## Security

### Network Security
```xml
<network-security-config>
    <!-- Allow localhost for development -->
    <domain-config cleartextTrafficPermitted="true">
        <domain>localhost</domain>
    </domain-config>

    <!-- Production: HTTPS only -->
    <domain-config cleartextTrafficPermitted="false">
        <domain>chat.mycoder.local</domain>
    </domain-config>
</network-security-config>
```

### Data Encryption
- SQLCipher for database encryption (future)
- Encrypted SharedPreferences for tokens
- Certificate pinning for production

### ProGuard/R8
- Code obfuscation in release builds
- Shrinking and optimization
- Keep rules for Retrofit, Room, Gson

## Testing Strategy

### Unit Tests
- ViewModels: Business logic
- Repository: Data operations
- Network: API client mocking
- Database: Room DAOs

### Integration Tests
- Repository + Database
- WebSocket connection
- API provider selection

### UI Tests
- Modern: Compose test framework
- Legacy: Espresso

## Performance Optimizations

### Memory Management
- LazyColumn/RecyclerView for efficient scrolling
- Image loading with Coil (size limits, caching)
- Room pagination for large message lists
- Proper lifecycle management to avoid leaks

### Network Optimization
- WebSocket connection pooling
- Message batching
- Offline queue with retry logic
- Request deduplication

### Battery Optimization
- JobScheduler for background sync
- WorkManager for deferred tasks
- Thermal monitoring to reduce CPU load
- Doze mode compatibility

## Future Enhancements

### Short-term
1. Firebase Cloud Messaging integration
2. Push notifications
3. File attachments support
4. Voice messages
5. QR code login

### Long-term
1. End-to-end encryption
2. Video/audio calls via WebRTC
3. Advanced AI features (image generation, code completion)
4. Multi-server support
5. Wear OS companion app

## Compatibility Matrix

| Feature | Modern | Legacy | Notes |
|---------|--------|--------|-------|
| Jetpack Compose | ✅ | ❌ | Modern only |
| XML Layouts | ❌ | ✅ | Legacy only |
| Material Design 3 | ✅ | ⚠️ | Limited in legacy |
| Thermal Monitoring | ✅ | ⚠️ | Fallback mode |
| Biometric Auth | ✅ | ❌ | Modern only |
| MultiDex | ❌ | ✅ | Legacy needs it |
| Desugaring | ❌ | ✅ | Java 8+ APIs |
| Min Android Version | 10 | 4.4 | API 29 vs 19 |

## Conclusion

This architecture provides:
- **Flexibility**: Dual variant support for wide device compatibility
- **Scalability**: Clean separation of concerns via MVVM + Repository
- **Performance**: Offline-first with optimized data flows
- **Maintainability**: Shared codebase with variant-specific overrides
- **Integration**: Seamless connection to MyCoder v2.1.0 backend
- **Production-Ready**: Comprehensive error handling, testing, and monitoring
