# Voice Features - MyCoder RocketChat

Kompletní hlasové ovládání pro mobilní aplikaci - **diktování hlasem** (Speech-to-Text) a **čtení odpovědí** (Text-to-Speech).

## 🎤 Funkce

### Speech-to-Text (STT)
- **Diktování zpráv**: Místo psaní na klávesnici mluvte do mikrofonu
- **Real-time zobrazení**: Průběžné zobrazení rozpoznávaného textu
- **Podpora češtiny**: Výchozí jazyk Czech (cs-CZ)
- **Offline kompatibilita**: Funguje offline (závislé na zařízení)
- **Chybové hlášení**: Přehledná zpráva o problémech

### Text-to-Speech (TTS)
- **Přehrávání odpovědí**: AI odpovědi se dají poslouchat místo čtení
- **Ovládání**: Tlačítko play/stop pro každou zprávu
- **Podpora češtiny**: Výchozí jazyk Czech (cs-CZ)
- **Nastavitelná rychlost**: Rychlost řeči 0.5x - 2.0x
- **Nastavitelná výška hlasu**: Pitch 0.5x - 2.0x

## 🏗️ Architektura

### Services

#### SpeechRecognitionService
```kotlin
class SpeechRecognitionService {
    // State flows
    val listeningState: StateFlow<ListeningState>
    val partialResults: StateFlow<String>
    val finalResults: StateFlow<SpeechResult?>
    val error: StateFlow<String?>

    // Methods
    fun startListening(language: String = "cs-CZ")
    fun stopListening()
    fun cancel()
}
```

**States:**
- `IDLE`: Nenahrává
- `LISTENING`: Aktivně nahrává
- `PROCESSING`: Zpracovává řeč
- `ERROR`: Chyba

#### TextToSpeechService
```kotlin
class TextToSpeechService {
    // State flows
    val speakingState: StateFlow<SpeakingState>
    val error: StateFlow<String?>

    // Settings
    var speechRate: Float  // 0.5f - 2.0f
    var pitch: Float       // 0.5f - 2.0f
    var language: Locale

    // Methods
    fun speak(text: String)
    fun speakQueued(text: String)
    fun stop()
}
```

**States:**
- `IDLE`: Nemluví
- `SPEAKING`: Aktivně mluví
- `ERROR`: Chyba

### UI Components

#### Modern Variant (Jetpack Compose)

**VoiceInputButton:**
```kotlin
@Composable
fun VoiceInputButton(
    onTextRecognized: (String) -> Unit,
    enabled: Boolean = true
)
```

Features:
- Automatická permission handling (RECORD_AUDIO)
- Pulsing animace při nahrávání
- Real-time partial results
- Error snackbar

**TextToSpeechButton:**
```kotlin
@Composable
fun TextToSpeechButton(
    text: String,
    enabled: Boolean = true
)
```

Features:
- Play/stop toggle
- Visual feedback při mluvení
- Error snackbar

#### Legacy Variant (XML + Fragments)

**XML Layouts:**
- `fragment_chat.xml`: Přidán `voice_button` (mikrofon)
- `item_message.xml`: Přidán `speak_button` (reproduktor) pro AI zprávy

**Fragments:**
- Implementace voice features v Fragment lifecycle
- Permission handling pomocí `ActivityResultContracts`

## 🔧 Použití

### Modern Variant (Compose)

```kotlin
// V ChatScreen
MessageInput(
    text = messageText,
    onTextChange = { messageText = it },  // Voice recognition sem dá text
    onSend = { viewModel.sendMessage(messageText) },
    // ...
)

// V MessageItem (AI zprávy)
if (message.isAiGenerated) {
    TextToSpeechButton(
        text = message.message
    )
}
```

### Legacy Variant (XML)

```kotlin
// V Fragment onCreate/onViewCreated
val voiceButton = view.findViewById<ImageButton>(R.id.voice_button)
val messageInput = view.findViewById<EditText>(R.id.message_input)

voiceButton.setOnClickListener {
    speechRecognition.startListening("cs-CZ")
}

// Observe results
lifecycleScope.launch {
    speechRecognition.finalResults.collect { result ->
        result?.let {
            messageInput.setText(it.text)
        }
    }
}
```

## 📱 Kompatibilita

### Android Versions

| Feature | Modern (API 29+) | Legacy (API 19+) |
|---------|------------------|------------------|
| Speech Recognition | ✅ Full | ✅ Full |
| Text-to-Speech | ✅ Full | ✅ Full |
| Partial Results | ✅ Yes | ✅ Yes |
| Offline Mode | ✅ Device-dependent | ✅ Device-dependent |
| Permission Handling | ✅ Runtime | ✅ Runtime |

### Supported Languages

Speech Recognition podporuje všechny jazyky, které má zařízení nainstalované:
- `cs-CZ` - Čeština (výchozí)
- `en-US` - Angličtina
- `sk-SK` - Slovenština
- ... a další podle zařízení

Text-to-Speech podporuje:
- `cs-CZ` - Čeština (výchozí)
- `en-US` - Angličtina
- ... a další podle nainstalovaných TTS enginů

## 🔐 Permissions

### AndroidManifest.xml
```xml
<!-- Audio permissions -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-feature android:name="android.hardware.microphone" android:required="false" />
```

### Runtime Permission Handling

Modern variant (Compose):
```kotlin
val permissionLauncher = rememberLauncherForActivityResult(
    ActivityResultContracts.RequestPermission()
) { isGranted ->
    if (isGranted) {
        speechRecognition.startListening("cs-CZ")
    }
}
```

Legacy variant (Fragment):
```kotlin
val requestPermissionLauncher = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
) { isGranted ->
    if (isGranted) {
        startVoiceInput()
    }
}
```

## ⚙️ Configuration

### Speech Recognition

**Změna jazyka:**
```kotlin
speechRecognition.startListening("en-US")  // English
speechRecognition.startListening("sk-SK")  // Slovak
```

**Check availability:**
```kotlin
if (speechRecognition.isAvailable()) {
    // Speech recognition is available
}
```

### Text-to-Speech

**Změna rychlosti řeči:**
```kotlin
textToSpeech.speechRate = 1.5f  // 1.5x rychleji
textToSpeech.speechRate = 0.75f // 0.75x pomaleji
```

**Změna výšky hlasu:**
```kotlin
textToSpeech.pitch = 1.2f  // Vyšší hlas
textToSpeech.pitch = 0.8f  // Nižší hlas
```

**Změna jazyka:**
```kotlin
textToSpeech.language = Locale("en", "US")  // English
textToSpeech.language = Locale("sk", "SK")  // Slovak
```

**Fronta zpráv:**
```kotlin
// Přeruší aktuální a mluví novou
textToSpeech.speak("První zpráva")

// Přidá do fronty (nemluví hned)
textToSpeech.speakQueued("Druhá zpráva")
```

## 🎯 Best Practices

### 1. Lifecycle Management

**Modern (Compose):**
```kotlin
// Services jsou singleton, lifecycle se spravuje automaticky
// Používejte collectAsStateWithLifecycle() pro flows
```

**Legacy (Fragment):**
```kotlin
override fun onDestroyView() {
    super.onDestroyView()
    // Services jsou singleton, ale můžete zastavit aktivní operace
    speechRecognition.cancel()
    textToSpeech.stop()
}
```

### 2. Error Handling

```kotlin
// Modern (Compose)
val error by speechRecognition.error.collectAsStateWithLifecycle()

error?.let { errorMessage ->
    Snackbar(...) {
        Text(errorMessage)
    }
}

// Legacy (Fragment)
lifecycleScope.launch {
    speechRecognition.error.collect { error ->
        error?.let {
            Toast.makeText(context, it, Toast.LENGTH_LONG).show()
        }
    }
}
```

### 3. User Feedback

**Během nahrávání:**
- Modern: Pulsing animace + partial results
- Legacy: ProgressBar + TextView pro partial results

**Během mluvení:**
- Modern: Změna ikony (VolumeUp → VolumeOff)
- Legacy: Změna ikony + colorFilter

## 🐛 Troubleshooting

### Speech Recognition nefunguje

**Problem:** "Speech recognition not available"

**Solution:**
1. Zkontrolujte, že zařízení má Google app nainstalovanou
2. Zkontrolujte internetové připojení (některá zařízení vyžadují online)
3. Zkontrolujte permissions v Settings

**Problem:** "No speech match found"

**Solution:**
1. Mluvte jasně a pomalu
2. Snižte background noise
3. Zkuste jiný jazyk

### Text-to-Speech nefunguje

**Problem:** "TTS initialization failed"

**Solution:**
1. Zkontrolujte, že zařízení má TTS engine nainstalovaný
2. Settings → Accessibility → Text-to-speech output
3. Nainstalujte Google Text-to-Speech z Play Store

**Problem:** "Language not supported"

**Solution:**
1. Settings → Language & input → Text-to-speech output
2. Stáhněte language data pro požadovaný jazyk

## 📊 Performance

### Memory Usage
- **SpeechRecognitionService**: ~5-10 MB (+ system recognizer)
- **TextToSpeechService**: ~3-5 MB (+ TTS engine)

### Battery Impact
- **Speech Recognition**: Střední (používá mikrofon + CPU)
- **Text-to-Speech**: Nízký (jen audio playback)

### Recommendations
- Používejte `cancel()` když není potřeba nahrávat
- Používejte `stop()` pro TTS když uživatel opouští screen
- Nezapomeňte na permission handling

## 🚀 Future Enhancements

### Plánované funkce:
1. **Voice commands**: "Pošli zprávu", "Otevři nastavení"
2. **Multiple language detection**: Automatická detekce jazyka
3. **Voice profiles**: Různé hlasy pro různé uživatele
4. **Offline TTS**: Embedded TTS engine
5. **Continuous recognition**: Neustálé nahrávání bez tlačítka
6. **Wake word**: "Hey MyCoder"

## 📖 References

- [Android SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer)
- [Android TextToSpeech](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
- [Speech Input Best Practices](https://developer.android.com/guide/topics/text/voice-input)

## 💡 Tips pro uživatele

### Pro nejlepší rozpoznávání:
1. **Mluvte jasně** a přirozenou rychlostí
2. **Pauza mezi větami** - systém lépe rozpozná hranice
3. **Tichý prostor** - minimalizujte background noise
4. **Držte telefon blízko** - ideálně 15-30 cm od úst

### Pro nejlepší přehrávání:
1. **Poslouchejte delší odpovědi** - šetří zrak
2. **Nastavte rychlost** - podle vašeho tempa
3. **Používejte v autě** - handsfree provoz
4. **Multitasking** - poslouchejte při jiných činnostech

---

**Vytvořeno pro MyCoder-v2.0**
Voice features kompatibilní s Android 4.4+ (API 19+)
