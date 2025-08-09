#!/bin/bash
set -e

echo "🚀 MyCoder Development Container Starting"
echo "========================================"
echo "🔥 LIVE RELOAD MODE - změny se projeví okamžitě!"
echo ""

# Development environment info
echo "📊 Development Environment:"
echo "   🐍 Python: $(python --version)"
echo "   📦 Poetry: $(poetry --version 2>/dev/null || echo 'Not available')"
echo "   🤖 Ollama: $(ollama --version 2>/dev/null || echo 'Starting...')"
echo "   📂 Working Dir: $(pwd)"
echo "   👤 User: $(whoami)"
echo ""

# Start Ollama service in background
echo "🚀 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
echo "   Ollama PID: $OLLAMA_PID"

# Wait for Ollama to be ready (faster timeout for dev)
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..15}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Attempt $i/15..."
    sleep 1
done

# Check if Ollama started successfully
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama failed to start within timeout"
    echo "🔧 Trying to start Ollama manually..."
    pkill ollama 2>/dev/null || true
    sleep 2
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
fi

# Pull DeepSeek model (with progress for dev)
echo "🔍 Checking for DeepSeek model..."
if ! ollama list | grep -q "deepseek-coder"; then
    echo "📥 Pulling DeepSeek Coder model for development..."
    echo "   This is one-time setup - subsequent starts will be fast!"
    ollama pull deepseek-coder:1.3b-base-q4_0 && echo "✅ DeepSeek model ready!"
else
    echo "✅ DeepSeek model already available"
fi

# Show available models
echo ""
echo "🤖 Available models:"
ollama list | tail -n +2 | while read line; do
    echo "   • $line"
done

# Development-specific setup
echo ""
echo "🔧 Development Setup:"

# Check if source code is mounted
if [ -d "/app/src" ] && [ "$(ls -A /app/src 2>/dev/null)" ]; then
    echo "   ✅ Source code mounted (live reload active)"
    ls -la /app/src | head -5
else
    echo "   ⚠️  Source code not mounted - live reload disabled"
fi

# Check for .env.dev
if [ -f "/app/.env" ]; then
    echo "   ✅ Development environment loaded"
    echo "   📋 Key settings:"
    grep -E "MYCODER_|OLLAMA_|LOG_LEVEL" /app/.env | head -5 | sed 's/^/      /'
else
    echo "   ⚠️  No .env file found"
fi

# Python path info  
echo "   🐍 Python path: $PYTHONPATH"
echo "   🔍 Can import mycoder: $(python -c 'import src.mycoder; print("✅ YES")' 2>/dev/null || echo '❌ NO')"

# Start development server
echo ""
echo "🌟 MyCoder Development Server Starting!"
echo "========================================"
echo "🔗 APIs available:"
echo "   • Ollama: http://localhost:11434"
echo "   • MyCoder: http://localhost:8000"  
echo "   • Debugger: localhost:5678"
echo ""
echo "🚀 Development Commands:"
echo "   docker-compose -f docker-compose.dev.yml exec mycoder-dev bash"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo "   make dev-shell  # if using Makefile"
echo ""

# Check if we should start in interactive mode or service mode
if [ "$1" = "interactive" ] || [ "$MYCODER_DEV_MODE" = "interactive" ]; then
    echo "🐍 Starting interactive Python session..."
    python -c "
import sys
sys.path.insert(0, '/app/src')
print('🎯 MyCoder Development Session')
print('Available modules:')
try:
    from src.mycoder import MyCoder
    print('  • MyCoder ✅')
except ImportError as e:
    print(f'  • MyCoder ❌ ({e})')

try:
    from src.ollama_integration import OllamaClient, CodeGenerationProvider
    print('  • Ollama Integration ✅')
except ImportError as e:
    print(f'  • Ollama Integration ❌ ({e})')

print('\\nQuick test:')
import asyncio

async def test():
    from src.ollama_integration import OllamaClient
    async with OllamaClient() as client:
        available = await client.is_available()
        print(f'Ollama connection: {\"✅ OK\" if available else \"❌ FAILED\"}')
        
        if available:
            models = await client.list_models()
            print(f'Models available: {len(models)}')

try:
    asyncio.run(test())
except Exception as e:
    print(f'Test failed: {e}')

print('\\n🚀 Ready for development!')
print('Pro debugging: import ipdb; ipdb.set_trace()')
"
    
    # Keep container running  
    echo ""
    echo "💤 Container running in development mode..."
    echo "   Press Ctrl+C to stop"
    trap 'echo "🛑 Stopping development server..."; kill $OLLAMA_PID 2>/dev/null; exit 0' INT TERM
    
    # Optional: Start file watcher
    if [ "$WATCHDOG_ENABLED" = "true" ]; then
        echo "👀 Starting file watcher..."
        python -c "
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os

class CodeChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.yml', '.yaml', '.json')):
            print(f'🔄 File changed: {event.src_path}')
            print('   Code is live-reloaded automatically!')

observer = Observer()
if os.path.exists('/app/src'):
    observer.schedule(CodeChangeHandler(), '/app/src', recursive=True)
    print('📂 Watching /app/src for changes...')
    observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    print('👀 File watcher stopped')
observer.join()
" &
    fi
    
    wait

elif [ "$1" = "test" ]; then
    echo "🧪 Running development tests..."
    if [ -d "/app/tests" ]; then
        python -m pytest /app/tests -v --tb=short
    else
        echo "⚠️  No tests directory found"
        python -c "
import sys
sys.path.insert(0, '/app/src')
from src.ollama_integration import OllamaClient
import asyncio

async def quick_test():
    print('🔍 Quick integration test...')
    async with OllamaClient() as client:
        if await client.is_available():
            print('✅ Ollama connection OK')
            models = await client.list_models()
            print(f'✅ Found {len(models)} models')
            return True
        else:
            print('❌ Ollama connection failed')
            return False

result = asyncio.run(quick_test())
exit(0 if result else 1)
"
    fi

elif [ "$1" = "demo" ]; then
    echo "🎬 Running MyCoder demo..."
    python -c "
import sys
sys.path.insert(0, '/app/src')
print('🎯 MyCoder Development Demo')
# Add demo code here
"

else
    # Default: run service mode
    echo "🌐 Starting MyCoder service (development mode)..."
    
    # Keep container alive and responsive
    trap 'echo "🛑 Stopping services..."; kill $OLLAMA_PID 2>/dev/null; exit 0' INT TERM
    
    # Start MyCoder in background
    python -c "
import sys
sys.path.insert(0, '/app/src')
import asyncio
import signal

async def run_mycoder():
    try:
        from src.mycoder import MyCoder
        print('🎯 Starting MyCoder service...')
        mycoder = MyCoder()
        print(f'✅ MyCoder ready in mode: {getattr(mycoder.mode_manager.current_mode, \"value\", \"unknown\")}')
        
        # Keep service running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print('🛑 MyCoder service stopped')
    except Exception as e:
        print(f'❌ MyCoder service error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(run_mycoder())
" &
    
    echo "💤 Services running... Press Ctrl+C to stop"
    wait
fi