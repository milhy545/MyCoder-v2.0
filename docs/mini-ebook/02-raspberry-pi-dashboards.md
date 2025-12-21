# Kapitola 2: Raspberry Pi Dashboard Koncepty

## Úvod

Raspberry Pi s touchscreen displejem je ideální platforma pro různé typy dashboardů. V této kapitole probereme 6 různých konceptů, jejich implementaci a hardware požadavky.

---

## Hardware setup

### Doporučená konfigurace

**Raspberry Pi 3B+ upgrade options:**
```
Base: Raspberry Pi 3B (1GB RAM, 4× Cortex-A53 @ 1.2GHz)
├─ Display: 7" touchscreen (800×480) - $60
├─ Storage: NVMe SSD 128GB via USB adapter - $30
├─ Case: 3D printed nebo FLIRC - $15
└─ Power: 5V/3A official PSU - $10

Total: ~$115 (+ RPi cena)
```

**NVMe na Raspberry Pi 3B:**
⚠️ **Důležité:** RPi 3B nemá PCIe, ale můžete použít:
```
NVMe SSD → M.2 to USB 3.0 adapter → RPi USB 2.0 port
```

**Výkon:**
- USB 2.0 = max 480 Mbps (60 MB/s teoreticky)
- Reálně: ~35-40 MB/s (stále 10x rychlejší než SD karta)
- Latence: <1ms (vs SD karta ~10ms)
- Spolehlivost: 100x lepší než SD karta

**Je to worth it?**
- ✅ ANO pro OS a databáze (random access)
- ✅ ANO pro životnost (SD karty umírají)
- ❌ NE pro streaming media (sequential read, SD stačí)

---

## Dashboard Koncept #1: Control Center

### Účel
Centrální ovládací panel pro celý domácí tech stack - MyCoder, servery, smart home, síť.

### Screenshot ASCII mockup
```
┌─────────────────────────────────────────────────────┐
│ 🏠 MyCoder Control Center      🔋 85%  📶 WiFi  12:34│
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐         │
│ │ 🖥️ Server  │ │ 🤖 MyCoder│ │ 🌡️ Thermal │         │
│ │  ONLINE   │ │  READY    │ │  Q9550    │         │
│ │  ●        │ │  ●        │ │  62°C     │         │
│ └───────────┘ └───────────┘ └───────────┘         │
│                                                     │
│ ┌─────────────────────────────────────────┐        │
│ │ 📊 System Stats                         │        │
│ │ CPU: ████████░░ 80%                     │        │
│ │ RAM: ██████░░░░ 65%                     │        │
│ │ Disk: ███░░░░░░░ 32%                    │        │
│ │ Net: ↓ 5.2 MB/s  ↑ 1.3 MB/s            │        │
│ └─────────────────────────────────────────┘        │
│                                                     │
│ ┌─────────────────────────────────────────┐        │
│ │ 🚀 Quick Actions                        │        │
│ │ [Restart MyCoder] [Update] [Backup]     │        │
│ └─────────────────────────────────────────┘        │
│                                                     │
│ Recent logs:                                        │
│ 12:31 - MyCoder: Task completed successfully        │
│ 12:28 - Thermal: Q9550 temp stable at 61°C         │
│ 12:25 - Network: Speed test 100/20 Mbps            │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

```python
# dashboard.py - Flask web server
from flask import Flask, render_template, jsonify
import psutil
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def stats():
    """Real-time system stats"""
    return jsonify({
        'cpu': psutil.cpu_percent(interval=1),
        'ram': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'network': {
            'sent': psutil.net_io_counters().bytes_sent,
            'recv': psutil.net_io_counters().bytes_recv
        },
        'temperature': get_q9550_temp()  # SSH to Q9550 box
    })

def get_q9550_temp():
    """Fetch Q9550 temperature via SSH"""
    result = subprocess.run(
        ['ssh', 'q9550box', 'sensors | grep "Core 0"'],
        capture_output=True, text=True
    )
    # Parse: "Core 0:        +62.0°C"
    return result.stdout.split('+')[1].split('°')[0]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

```html
<!-- templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>MyCoder Control Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            background: #1e1e1e;
            color: #fff;
            font-family: 'Segoe UI', sans-serif;
        }
        .card {
            background: #2d2d2d;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .online { background: #4caf50; }
        .offline { background: #f44336; }
    </style>
</head>
<body>
    <div id="app">
        <!-- Vue.js nebo vanilla JS dashboard -->
    </div>
    <script>
        // Fetch stats every 2 seconds
        setInterval(async () => {
            const response = await fetch('/api/stats');
            const data = await response.json();
            updateDashboard(data);
        }, 2000);
    </script>
</body>
</html>
```

### Features
- ✅ Real-time monitoring všech services
- ✅ Thermal monitoring Q9550
- ✅ Quick actions (restart, update, backup)
- ✅ Logs viewer
- ✅ Network stats
- ✅ Uptime tracking

### Hardware požadavky
- **CPU:** 10-15% (Flask + monitoring)
- **RAM:** 100-150 MB
- **Storage:** 50 MB (app + logs)
- **Network:** Minimal (jen local REST API)

---

## Dashboard Koncept #2: Home Automation Hub

### Účel
Ovládání smart home zařízení - světla, teplota, kamery, senzory.

### Integrace

**Home Assistant compatible:**
```yaml
# configuration.yaml pro Home Assistant
homeassistant:
  name: Home
  latitude: 50.0755
  longitude: 14.4378
  unit_system: metric
  time_zone: Europe/Prague

# Integrace
light:
  - platform: mqtt
    name: "Living Room"
    command_topic: "home/livingroom/light/set"

sensor:
  - platform: mqtt
    name: "Temperature"
    state_topic: "home/livingroom/temperature"
    unit_of_measurement: "°C"

camera:
  - platform: mjpeg
    name: "Front Door"
    mjpeg_url: http://192.168.1.150/video
```

**Dashboard na RPi touchscreen:**
```
┌─────────────────────────────────────────────────────┐
│ 🏡 Home Automation                    🌡️ 22°C  12:34│
├─────────────────────────────────────────────────────┤
│                                                     │
│ Living Room                                         │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│ │ 💡 Light │ │ 🌡️ Temp │ │ 📹 Cam  │               │
│ │  [ON]   │ │  22°C   │ │ [VIEW]  │               │
│ │ ●───O   │ │         │ │         │               │
│ └─────────┘ └─────────┘ └─────────┘               │
│                                                     │
│ Bedroom                                             │
│ ┌─────────┐ ┌─────────┐                           │
│ │ 💡 Light │ │ 🌡️ Temp │                           │
│ │  [OFF]  │ │  20°C   │                           │
│ │ O───●   │ │         │                           │
│ └─────────┘ └─────────┘                           │
│                                                     │
│ Scenes:                                             │
│ [🌅 Morning] [🌙 Night] [🎬 Movie] [🏠 Away]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Fullscreen kiosk mode

```bash
# ~/start_dashboard.sh
#!/bin/bash

# Disable screensaver
xset s off
xset -dpms
xset s noblank

# Start Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-features=TranslateUI \
    --disk-cache-dir=/dev/null \
    http://localhost:8123  # Home Assistant URL

# Auto-restart on crash
while true; do
    sleep 10
done
```

**Autostart při bootu:**
```bash
# ~/.config/autostart/dashboard.desktop
[Desktop Entry]
Type=Application
Name=Dashboard
Exec=/home/pi/start_dashboard.sh
X-GNOME-Autostart-enabled=true
```

### Features
- ✅ Touch-friendly UI
- ✅ Real-time device states
- ✅ Scenes a automation
- ✅ Camera feeds
- ✅ Energy monitoring
- ✅ Voice control integration (Whisper!)

---

## Dashboard Koncept #3: System Monitor

### Účel
Monitoring všech serverů, služeb a infrastruktury - Grafana style.

### Stack: Prometheus + Grafana

```yaml
# docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

  node_exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'raspberry-pi'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'q9550-server'
    static_configs:
      - targets: ['192.168.1.100:9100']

  - job_name: 'mycoder-api'
    static_configs:
      - targets: ['192.168.1.100:8000']
```

### Grafana Dashboard

**Pre-made dashboard IDs:**
- **Node Exporter Full:** 1860
- **Docker monitoring:** 893
- **Network monitoring:** 11074

```bash
# Import dashboard via API
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "uid": "mycoder-overview",
      "title": "MyCoder System Overview"
    },
    "inputs": [{
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    }],
    "overwrite": true
  }'
```

### RPi jako display terminal

```python
# grafana_viewer.py - Auto-rotate dashboards
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

dashboards = [
    'http://localhost:3000/d/overview',
    'http://localhost:3000/d/q9550-thermal',
    'http://localhost:3000/d/network',
    'http://localhost:3000/d/mycoder-stats'
]

chrome_options = Options()
chrome_options.add_argument('--kiosk')
chrome_options.add_argument('--disable-infobars')

driver = webdriver.Chrome(options=chrome_options)

while True:
    for dashboard in dashboards:
        driver.get(dashboard)
        time.sleep(30)  # Show each dashboard for 30s
```

### Features
- ✅ Multi-server monitoring
- ✅ Historical data (Prometheus retention)
- ✅ Alerts (email, Slack, Discord)
- ✅ Custom metrics
- ✅ Beautiful graphs

### Hardware požadavky (RPi 3B)
- **CPU:** 20-30% (Prometheus scraping)
- **RAM:** 300-400 MB (Prometheus + Grafana)
- **Storage:** 2-5 GB (metrics retention)
- **⚠️ Warning:** Může být na hraně, zvažte offload Prometheus na jiný stroj

---

## Dashboard Koncept #4: Media Center

### Účel
Kodi/Jellyfin media player s touchscreen ovládáním.

### Option A: Kodi

```bash
# Instalace Kodi na Raspberry Pi OS
sudo apt update
sudo apt install kodi

# Auto-start Kodi
sudo systemctl enable kodi@pi
sudo systemctl start kodi@pi
```

**Optimalizace pro RPi 3B:**
```xml
<!-- ~/.kodi/userdata/advancedsettings.xml -->
<advancedsettings>
    <network>
        <buffermode>1</buffermode>
        <cachemembuffersize>20971520</cachemembuffersize>
        <readbufferfactor>4.0</readbufferfactor>
    </network>
    <video>
        <latency>100</latency>
    </video>
</advancedsettings>
```

### Option B: Jellyfin Client

```bash
# Instalace Jellyfin
curl https://repo.jellyfin.org/install-debuntu.sh | sudo bash

# Web interface
http://localhost:8096

# Pro touchscreen: Chromium kiosk mode
chromium-browser --kiosk http://localhost:8096
```

### Hardware limits (RPi 3B)

**Video playback možnosti:**

| Codec | Resolution | FPS | Možné? |
|-------|------------|-----|--------|
| H.264 | 1080p | 30 | ✅ HW decode |
| H.264 | 1080p | 60 | ❌ CPU throttle |
| H.265/HEVC | 1080p | 30 | ❌ No HW decode |
| VP9 | 1080p | 30 | ❌ No HW decode |
| AV1 | any | any | ❌ No HW decode |

**Závěr:** RPi 3B je OK pro 1080p H.264, ale nic moderního (HEVC, VP9, AV1).

**Doporučení:** Použít RPi 4 (4GB+) nebo LibreELEC místo Raspberry Pi OS.

---

## Dashboard Koncept #5: AI Assistant Display

### Účel
Dedicated displej pro MyCoder AI conversations, jako "physical ChatGPT".

### Koncept

```
┌─────────────────────────────────────────────────────┐
│ 🤖 MyCoder AI Assistant                       12:34 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ You: Analyze temperature trends for Q9550           │
│                                                     │
│ MyCoder: Based on PowerManagement logs, I've       │
│ analyzed the Q9550 temperature over the last       │
│ 24 hours:                                          │
│                                                     │
│ - Average: 58°C                                    │
│ - Peak: 73°C (during LLM inference)                │
│ - Idle: 45°C                                       │
│                                                     │
│ Recommendation: Current cooling is adequate.        │
│ Consider thermal paste replacement if peaks >80°C.  │
│                                                     │
│ ┌─────────────────────────────────────────┐        │
│ │ [🎤 Voice Query]  [⌨️ Type]  [🔄 Retry]  │        │
│ └─────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────┘
```

### Implementation

```python
# ai_display.py - Flask app pro AI chat
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

MYCODER_API = 'http://192.168.1.100:8000'  # Váš MyCoder server

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/query', methods=['POST'])
def query():
    """Forward query to MyCoder API"""
    user_message = request.json['message']

    response = requests.post(
        f'{MYCODER_API}/api/chat',
        json={
            'message': user_message,
            'provider': 'claude_oauth',  # nebo auto-select
            'context': 'dashboard_query'
        }
    )

    return jsonify(response.json())

@app.route('/api/voice', methods=['POST'])
def voice_query():
    """Transcribe audio via Whisper then query MyCoder"""
    audio_file = request.files['audio']

    # Option 1: Use whisper.cpp locally
    transcription = transcribe_local(audio_file)

    # Option 2: Use Whisper API
    # transcription = transcribe_openai(audio_file)

    # Send to MyCoder
    return query({'message': transcription})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Voice integration

```javascript
// Record audio from browser
let mediaRecorder;
let audioChunks = [];

async function startVoiceQuery() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        const formData = new FormData();
        formData.append('audio', audioBlob);

        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        displayResponse(result);

        audioChunks = [];
    };

    mediaRecorder.start();
}

function stopVoiceQuery() {
    mediaRecorder.stop();
}
```

### Features
- ✅ Voice queries (Whisper integration)
- ✅ Text-to-Speech responses
- ✅ Conversation history
- ✅ Multi-provider support (Claude, Gemini, Ollama)
- ✅ Thermal-aware (shows Q9550 temp)

---

## Dashboard Koncept #6: Development Dashboard

### Účel
Monitoring GitHub repos, CI/CD pipelines, test results, code metrics.

### Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Code metrics
  sonarqube:
    image: sonarqube:community
    ports:
      - "9000:9000"
    environment:
      - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true

  # CI/CD monitoring
  jenkins:
    image: jenkins/jenkins:lts
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_data:/var/jenkins_home

  # Git stats
  gitea:
    image: gitea/gitea:latest
    ports:
      - "3000:3000"
      - "222:22"
    volumes:
      - gitea_data:/data

volumes:
  jenkins_data:
  gitea_data:
```

### Dashboard display

```
┌─────────────────────────────────────────────────────┐
│ 💻 Development Overview                       12:34 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📦 MyCoder-v2.0                                     │
│ ├─ Last commit: 2 hours ago                        │
│ ├─ Tests: ✅ 127 passed, ❌ 3 failed                │
│ ├─ Coverage: 85%                                   │
│ └─ Build: ✅ SUCCESS                                │
│                                                     │
│ 📱 Android RocketChat                               │
│ ├─ Last commit: 5 hours ago                        │
│ ├─ Tests: ✅ 89 passed                              │
│ ├─ APK size: 45.2 MB                               │
│ └─ Build: 🔄 IN PROGRESS                            │
│                                                     │
│ 📊 Code Quality (SonarQube)                         │
│ ├─ Bugs: 2 🐛                                       │
│ ├─ Vulnerabilities: 0 🔒                           │
│ ├─ Code Smells: 15 👃                               │
│ └─ Tech Debt: 2h 30m                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### GitHub API integration

```python
# github_monitor.py
import requests
from datetime import datetime

GITHUB_TOKEN = 'your_github_token'
REPOS = ['yourusername/MyCoder-v2.0', 'yourusername/android-app']

def get_repo_stats(repo):
    """Fetch repo stats from GitHub API"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    # Latest commit
    commits = requests.get(
        f'https://api.github.com/repos/{repo}/commits',
        headers=headers
    ).json()

    last_commit = commits[0]['commit']['message']
    last_commit_time = commits[0]['commit']['author']['date']

    # Workflow runs (CI/CD)
    workflows = requests.get(
        f'https://api.github.com/repos/{repo}/actions/runs',
        headers=headers
    ).json()

    latest_run = workflows['workflow_runs'][0]
    build_status = latest_run['conclusion']  # 'success', 'failure', etc.

    return {
        'last_commit': last_commit,
        'last_commit_time': last_commit_time,
        'build_status': build_status
    }
```

---

## Multi-Dashboard switcher

### Auto-rotate mezi dashboardy

```python
# dashboard_rotator.py
import time
import subprocess

DASHBOARDS = [
    ('Control Center', 'http://localhost:8080'),
    ('System Monitor', 'http://localhost:3000'),
    ('AI Assistant', 'http://localhost:5000'),
    ('Development', 'http://localhost:9000'),
]

DISPLAY_TIME = 30  # seconds per dashboard

def switch_dashboard(url):
    """Switch browser to different dashboard"""
    # Using wmctrl to focus window
    subprocess.run(['wmctrl', '-a', 'Chromium'])
    # Send Ctrl+L (focus URL bar) + URL + Enter
    subprocess.run(['xdotool', 'key', 'ctrl+l'])
    time.sleep(0.1)
    subprocess.run(['xdotool', 'type', url])
    subprocess.run(['xdotool', 'key', 'Return'])

if __name__ == '__main__':
    while True:
        for name, url in DASHBOARDS:
            print(f"Switching to: {name}")
            switch_dashboard(url)
            time.sleep(DISPLAY_TIME)
```

---

## Hardware Comparison: RPi 3B vs RPi 4

| Feature | RPi 3B | RPi 4 (4GB) | Doporučení |
|---------|---------|-------------|------------|
| RAM | 1 GB | 4 GB | 4 je 4x lepší pro dashboardy |
| CPU | 1.2 GHz | 1.5 GHz | Marginal difference |
| USB | USB 2.0 | USB 3.0 | 4 má lepší NVMe performance |
| Network | 100 Mbps | 1 Gbps | 4 je nutné pro remote monitoring |
| Video | 1080p30 | 4K60 | 4 pokud máte 4K display |
| Cena | ~$35 | ~$55 | +$20 je worth it |

**Závěr:** Pro dashboardy s více službami (Grafana + HA + AI) doporučuji **RPi 4 (4GB)**.

RPi 3B funguje pro:
- ✅ Jeden dashboard (Home Assistant NEBO Grafana)
- ✅ Kiosk mode (jen browser)
- ✅ AI Assistant display (lightweight)

RPi 3B je tight pro:
- ❌ Multiple services současně
- ❌ Grafana s velkým retention
- ❌ Heavy web apps

---

## Závěr - Co postavit?

### Moje doporučení pro váš use-case:

**Setup #1: AI Assistant Terminal** (RPi 3B OK)
```
Raspberry Pi 3B + 7" touchscreen + NVMe SSD
├─ Flask web app (lightweight)
├─ Voice input (browser WebRTC)
├─ Whisper API (offload na main server)
└─ MyCoder API client

Total RAM: ~200 MB
Total CPU: 15-20%
```

**Setup #2: Control Center** (RPi 4 lepší)
```
Raspberry Pi 4 (4GB) + 7" touchscreen
├─ Flask dashboard
├─ Prometheus + Grafana
├─ Home Assistant
└─ Auto-rotate mezi views

Total RAM: ~800 MB (tight na 3B, OK na 4)
```

**Tip:** Začněte s **AI Assistant Terminal** - je to coolest a nejméně resource-hungry!

---

**Next:** [Kapitola 3 - MicroLLM Modely →](03-microllm-models.md)
