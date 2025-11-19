# MyCoder RocketChat - Android Mobile App

Production-ready Android application for RocketChat with MyCoder v2.0 AI integration.

## Features

### Dual API Level Support
- **Modern** (Android 10+, API 29+): Jetpack Compose with Material Design 3
- **Legacy** (Android 4.4+, API 19+): Traditional XML layouts with AppCompat

### Core Functionality
- **RocketChat Integration**: Real-time messaging via WebSocket
- **MyCoder v2.0 AI**: 5-tier API provider system integration
  - Claude Anthropic API
  - Claude OAuth
  - Gemini
  - Ollama Local
  - Ollama Remote
- **Thermal Awareness**: Integrated thermal monitoring for Q9550 and modern Android devices
- **Offline-First**: Room database with local caching
- **Multi-Provider AI**: Automatic provider selection based on thermal conditions

## Build Variants

### Modern (Android 10+)
```bash
./gradlew assembleModernDebug
./gradlew assembleModernRelease
```

**Features:**
- Jetpack Compose UI
- Material Design 3
- Biometric authentication support
- Advanced thermal monitoring (PowerManager API)
- Modern Android APIs

### Legacy (Android 4.4+)
```bash
./gradlew assembleLegacyDebug
./gradlew assembleLegacyRelease
```

**Features:**
- XML layouts with AppCompat
- Material Components (backwards compatible)
- MultiDex support
- Java 8+ desugaring for legacy compatibility
- Works on Android 4.4 KitKat and newer

## Project Structure

```
mobile/android/
├── app/
│   ├── src/
│   │   ├── main/                    # Shared code
│   │   │   ├── java/                # Main application code
│   │   │   │   └── com/mycoder/rocketchat/
│   │   │   │       ├── MyCoderApplication.kt
│   │   │   │       ├── data/        # Data layer
│   │   │   │       │   ├── model/   # Data models
│   │   │   │       │   ├── local/   # Room database
│   │   │   │       │   └── repository/
│   │   │   │       ├── network/     # Network layer
│   │   │   │       │   ├── MyCoderApiClient.kt
│   │   │   │       │   └── RocketChatWebSocket.kt
│   │   │   │       ├── service/     # Background services
│   │   │   │       └── ui/          # UI layer
│   │   │   │           └── viewmodel/
│   │   │   └── res/                 # Resources (layouts, strings, etc.)
│   │   ├── modern/                  # Modern variant (API 29+)
│   │   │   └── java/
│   │   │       └── com/mycoder/rocketchat/
│   │   │           └── ui/
│   │   │               ├── MainActivity.kt
│   │   │               └── compose/  # Jetpack Compose UI
│   │   └── legacy/                  # Legacy variant (API 19+)
│   │       └── java/
│   │           └── com/mycoder/rocketchat/
│   │               └── ui/
│   │                   └── fragments/  # Fragment-based UI
│   ├── build.gradle.kts
│   └── proguard-rules.pro
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

## Architecture

### MVVM Pattern
- **Model**: Data models, Room entities
- **View**: Jetpack Compose (modern) / XML + Fragments (legacy)
- **ViewModel**: ViewModels with StateFlow

### Repository Pattern
- **ChatRepository**: Centralized data access
- **Offline-First**: Local database as source of truth
- **Background Sync**: WebSocket for real-time updates

### Dependency Injection
- Manual DI via Application class
- Singleton pattern for repositories and network clients

## Configuration

### Build Configuration
Edit `app/build.gradle.kts`:

```kotlin
defaultConfig {
    buildConfigField("String", "MYCODER_API_URL", "\"http://your-server:8000\"")
    buildConfigField("String", "ROCKETCHAT_SERVER", "\"wss://your-chat-server\"")
}
```

### Runtime Configuration
The app reads configuration from:
- `BuildConfig` constants
- Shared Preferences (user settings)
- Environment variables (for development)

## Development

### Prerequisites
- Android Studio Hedgehog (2023.1.1) or newer
- JDK 17
- Android SDK with API 34
- Gradle 8.2+

### Setup
1. Clone repository:
   ```bash
   cd /home/user/MyCoder-v2.0/mobile/android
   ```

2. Sync Gradle:
   ```bash
   ./gradlew sync
   ```

3. Build:
   ```bash
   ./gradlew build
   ```

### Running
#### Modern variant (Android 10+)
```bash
./gradlew installModernDebug
adb shell am start -n com.mycoder.rocketchat.debug/.ui.MainActivity
```

#### Legacy variant (Android 4.4+)
```bash
./gradlew installLegacyDebug
adb shell am start -n com.mycoder.rocketchat.debug/.ui.MainActivity
```

## Testing

### Unit Tests
```bash
./gradlew testModernDebugUnitTest
./gradlew testLegacyDebugUnitTest
```

### Instrumentation Tests
```bash
./gradlew connectedModernDebugAndroidTest
./gradlew connectedLegacyDebugAndroidTest
```

## Thermal Monitoring

### Modern (Android 10+)
Uses `PowerManager.currentThermalStatus` for accurate thermal monitoring:
- `THERMAL_STATUS_NONE` → Normal operation
- `THERMAL_STATUS_MODERATE` → Prefer local AI providers
- `THERMAL_STATUS_SEVERE` → Use local-only
- `THERMAL_STATUS_CRITICAL` → Limit AI operations

### Legacy (Android 4.4+)
Falls back to power save mode detection:
- Normal mode → All providers available
- Power save mode → Prefer local providers

## Integration with MyCoder v2.0

The app communicates with MyCoder v2.0 backend via:

1. **REST API** (`MyCoderApiClient`):
   - `/api/v2/query` - AI queries
   - `/api/v2/status` - System status
   - `/api/v2/providers` - Available providers

2. **RocketChat WebSocket** (`RocketChatWebSocket`):
   - Real-time messaging
   - Custom method: `mycoder.query` for AI integration

## Deployment

### Release Build
1. Configure signing in `app/build.gradle.kts`
2. Build release APKs:
   ```bash
   ./gradlew assembleModernRelease
   ./gradlew assembleLegacyRelease
   ```

3. APKs location:
   - Modern: `app/build/outputs/apk/modern/release/app-modern-release.apk`
   - Legacy: `app/build/outputs/apk/legacy/release/app-legacy-release.apk`

### Distribution
- **Modern**: For Android 10+ devices (Play Store, F-Droid)
- **Legacy**: For older Android 4.4+ devices (direct APK distribution)

## Troubleshooting

### Common Issues

**Gradle sync fails:**
```bash
./gradlew clean
./gradlew sync
```

**MultiDex issues (legacy):**
- Ensure `multiDexEnabled = true` in `build.gradle.kts`
- Application extends `MultiDexApplication`

**WebSocket connection fails:**
- Check network security config in `res/xml/network_security_config.xml`
- Verify server URL in BuildConfig

**Thermal monitoring not working:**
- Modern: Requires Android 10+
- Legacy: Falls back to power save mode detection

## License

Part of MyCoder-v2.0 project.

## Contributing

1. Follow Kotlin coding conventions
2. Maintain compatibility with both variants
3. Add tests for new features
4. Update documentation

## Support

For issues and questions:
- GitHub Issues: https://github.com/milhy545/MyCoder-v2.0/issues
- Documentation: `../docs/`
