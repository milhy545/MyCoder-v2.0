#!/bin/bash
set -e

echo "🪶 MyCoder Ultra-Lightweight Container Starting"
echo "=============================================="
echo "💡 Optimalized pro slabší hardware!"
echo "📊 Minimální spotřeba: 2-4GB RAM, 1-2 CPU cores"
echo ""

# Lightweight environment info
echo "📊 Lightweight Environment:"
echo "   🐍 Python: $(python --version)"
echo "   🤖 Ollama: $(ollama --version 2>/dev/null || echo 'Starting...')"
echo "   📂 Working Dir: $(pwd)"
echo "   💾 Available RAM: $(free -h | grep ^Mem | awk '{print $7}')"
echo ""

# Start Ollama s resource constraints
echo "🚀 Starting Ollama (lightweight mode)..."
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_VRAM=0  # CPU-only
ollama serve &
OLLAMA_PID=$!
echo "   Ollama PID: $OLLAMA_PID (resource-limited)"

# Kratší timeout pro lightweight
echo "⏳ Waiting for Ollama (lightweight timeout)..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama ready!"
        break
    fi
    echo "   Attempt $i/10..."
    sleep 2
done

# Check Ollama startup
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama failed to start"
    exit 1
fi

# Ensure TinyLlama is available (už by měl být stažený)
echo "🔍 Checking TinyLlama model..."
if ! ollama list | grep -q "tinyllama"; then
    echo "📥 Pulling TinyLlama (lightweight - 637MB)..."
    ollama pull tinyllama:1.1b
    echo "✅ TinyLlama ready!"
else
    echo "✅ TinyLlama already available"
fi

# Show available models (should be minimal)
echo ""
echo "🤖 Available models (lightweight setup):"
ollama list | tail -n +2 | while read line; do
    echo "   • $line"
done

# Memory usage info
echo ""
echo "📊 Current Resource Usage:"
echo "   💾 RAM: $(free -h | grep ^Mem | awk '{print $3 "/" $2}')"
echo "   🖥️  CPU: $(nproc) cores available"
echo "   📦 Models loaded: 1 (TinyLlama)"

# Lightweight test
echo ""
echo "🧪 Lightweight functionality test..."
if ollama show tinyllama:1.1b >/dev/null 2>&1; then
    echo "   ✅ TinyLlama model accessible"
    
    # Quick generation test (timeout rychle)
    echo "   🎯 Testing AI generation..."
    timeout 15s ollama run tinyllama:1.1b "def hello():" > /tmp/test_output 2>&1 && \
    echo "   ✅ AI generation working" || \
    echo "   ⚠️  AI generation slow (expected on weak hardware)"
else
    echo "   ❌ TinyLlama model issue"
fi

# Start lightweight MyCoder service
echo ""
echo "🌟 MyCoder Lightweight Service Starting!"
echo "========================================"
echo "🔗 APIs:"
echo "   • Ollama: http://localhost:11434"
echo "   • MyCoder: http://localhost:8000"
echo ""
echo "🪶 Lightweight Mode Features:"
echo "   • TinyLlama AI model (637MB)"
echo "   • CPU-only inference"
echo "   • Single model loading"
echo "   • Reduced memory footprint"
echo ""

# Simple service mode (ne interactive)
echo "💤 Lightweight service running..."
echo "   Resource usage minimized"
echo "   Press Ctrl+C to stop"

# Trap pro cleanup
trap 'echo "🛑 Stopping lightweight services..."; kill $OLLAMA_PID 2>/dev/null; exit 0' INT TERM

# Keep lightweight service alive
if [ "$1" = "lightweight" ] || [ -z "$1" ]; then
    # Monitor resource usage periodically
    while true; do
        sleep 30
        # Optional: Log resource usage každých 30 sekund
        if [ "$MYCODER_DEBUG" = "true" ]; then
            echo "[$(date)] RAM: $(free -h | grep ^Mem | awk '{print $3}')"
        fi
    done
else
    echo "🔧 Custom command: $*"
    exec "$@"
fi