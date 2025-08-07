#!/bin/bash

# 🐳 MyCoder Docker Build Script

set -e

echo "🐳 MyCoder - Docker Build & Deploy"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker není nainstalován!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose není nainstalován!"
    exit 1
fi

print_status "Docker nalezen"

# Build options
BUILD_OPTION=${1:-"full"}

case $BUILD_OPTION in
    "quick")
        echo "🚀 Quick build (bez Ollama models)..."
        docker build -t mycoder:latest .
        ;;
    "full")
        echo "🚀 Full build s předstažením modelů..."
        docker build -t mycoder:latest .
        
        # Pre-pull models in separate container
        echo "📥 Předstahování Ollama modelů..."
        docker run --rm -d --name mycoder-setup \
            -v mycoder_models:/root/.ollama \
            ollama/ollama:latest
        
        # Wait for ollama to start
        sleep 10
        
        # Pull models
        models=("codellama:7b-instruct" "llama3.2:3b-instruct-q4_0")
        for model in "${models[@]}"; do
            echo "📥 Pulling $model..."
            docker exec mycoder-setup ollama pull "$model" || print_warning "Failed to pull $model"
        done
        
        # Cleanup
        docker stop mycoder-setup || true
        ;;
    "compose")
        echo "🏗️  Building with Docker Compose..."
        docker-compose build
        ;;
    *)
        echo "❓ Usage: $0 [quick|full|compose]"
        echo "   quick  - Fast build bez modelů"
        echo "   full   - Complete build s modely"
        echo "   compose - Build via docker-compose"
        exit 1
        ;;
esac

print_status "Build dokončen!"

echo
echo "🚀 SPUŠTĚNÍ:"
echo "   docker run -p 8000:8000 -p 11434:11434 mycoder:latest"
echo "   nebo"
echo "   docker-compose up"
echo
echo "🔗 ENDPOINTS:"
echo "   MyCoder:  http://localhost:8000"
echo "   Ollama:   http://localhost:11434"

print_status "Ready to code! 🤖"