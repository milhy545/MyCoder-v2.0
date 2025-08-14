#!/bin/bash
set -e

echo "🤖 MyCoder - Starting Docker Container"
echo "======================================"

# Start Ollama service in background
echo "🚀 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

# Pull DeepSeek Coder model first (optimized for Q9550 hardware)
echo "🔍 Checking for DeepSeek model..."
if ! ollama list | grep -q "deepseek-coder"; then
    echo "📥 Pulling DeepSeek Coder model (optimized, lightweight - 750MB)..."
    ollama pull deepseek-coder:1.3b-base-q4_0
    echo "✅ DeepSeek Coder model ready!"
else
    echo "✅ DeepSeek Coder model already available"
fi

# Fallback: Pull CodeLlama if DeepSeek fails
if ! ollama list | grep -q "deepseek-coder\|codellama"; then
    echo "📥 Pulling CodeLlama as fallback..."
    ollama pull codellama:7b-instruct-q4_0
fi

# Optional: Pull other useful models (in fallback order)
echo "🔍 Setting up additional models..."
models_to_pull=(
    "llama3.2:3b-instruct-q4_0"     # Fast, small model
    "codellama:7b-instruct-q4_0"    # Meta's code model (fallback)
)

for model in "${models_to_pull[@]}"; do
    if ! ollama list | grep -q "${model%%:*}"; then
        echo "📥 Pulling $model..."
        ollama pull "$model" || echo "⚠️  Failed to pull $model"
    fi
done

# Start MyCoder
echo "🎯 Starting MyCoder..."
echo "Available models:"
ollama list

# Keep container running and show logs
echo "🌟 MyCoder Docker container is ready!"
echo "======================================"
echo "🔗 Ollama API: http://localhost:11434"
echo "🤖 Available models:"
ollama list | tail -n +2
echo "======================================"

# Start interactive Python session or run specific command
if [ "$1" = "interactive" ]; then
    echo "🐍 Starting interactive Python session..."
    python -c "
from mycoder import MyCoder
import asyncio

async def main():
    mycoder = MyCoder()
    print('🎯 MyCoder ready with Ollama integration!')
    print(f'Current mode: {mycoder.mode_manager.current_mode.value}')
    
    # Test Ollama connection
    result = await mycoder.process_request('Hello from Docker! Create a simple Python function.')
    print('Response:', result.get('content', 'No response'))

if __name__ == '__main__':
    asyncio.run(main())
"
elif [ "$1" = "test" ]; then
    echo "🧪 Running MyCoder tests..."
    python -m pytest tests/ -v || echo "⚠️  Some tests may require external services"
elif [ "$1" = "demo" ]; then
    echo "🎬 Running MyCoder demo..."
    python quick_start.py
else
    # Keep container alive
    echo "💤 Container running... Press Ctrl+C to stop"
    trap 'echo "🛑 Stopping services..."; kill $OLLAMA_PID 2>/dev/null; exit 0' INT TERM
    wait
fi