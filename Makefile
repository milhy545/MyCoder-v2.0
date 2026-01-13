# 🚀 MyCoder Makefile - Snadné příkazy pro development a production
.PHONY: help dev prod build test clean logs shell debug stop restart status test-local lint-local format-local venv

# Výchozí target
.DEFAULT_GOAL := help

# Barvy pro výstup
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
RESET := \033[0m

# Docker Compose wrapper (plugin nebo standalone)
DOCKER_COMPOSE ?= docker compose
PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

##@ 🚀 MyCoder Development Commands

help: ## 📋 Zobraz tento help
	@echo "$(CYAN)🤖 MyCoder - Docker Development Helper$(RESET)"
	@echo "$(YELLOW)======================================$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(CYAN)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ 🔥 Development (Live Reload)

dev: ## 🚀 Spustí development server s live reload
	@echo "$(GREEN)🚀 Starting MyCoder Development Environment...$(RESET)"
	@echo "$(YELLOW)📂 Source code bude live-reloadován!$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build

dev-detached: ## 🌙 Spustí dev server na pozadí
	@echo "$(GREEN)🚀 Starting MyCoder Development (detached)...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build -d
	@echo "$(CYAN)💡 Use 'make logs' to see output$(RESET)"

dev-shell: ## 🐚 Otevři shell v development kontejneru
	@echo "$(GREEN)🐚 Opening development shell...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec mycoder-dev bash

dev-python: ## 🐍 Spustí Python shell v dev prostředí
	@echo "$(GREEN)🐍 Starting Python development shell...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec mycoder-dev python -c "\
		import sys; sys.path.insert(0, '/app/src'); \
		print('🎯 MyCoder Python Shell'); \
		print('Import: from mycoder import MyCoder'); \
		exec(open('/usr/lib/python3.11/code.py').read())"

debug: ## 🐛 Spustí s debugger portem (5678)
	@echo "$(GREEN)🐛 Starting with debugger support...$(RESET)"
	@echo "$(YELLOW)📡 Connect your IDE debugger to localhost:5678$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build mycoder-dev

##@ 🏭 Production

prod: ## 🏭 Spustí production server
	@echo "$(GREEN)🏭 Starting MyCoder Production Environment...$(RESET)"
	$(DOCKER_COMPOSE) up --build

prod-detached: ## 🌙 Spustí production na pozadí
	@echo "$(GREEN)🏭 Starting MyCoder Production (detached)...$(RESET)"
	$(DOCKER_COMPOSE) up --build -d
	@echo "$(CYAN)💡 Use 'make logs-prod' to see output$(RESET)"

##@ 🪶 Lightweight (pro slabší hardware)

light: ## 🪶 Ultra-lightweight verze (2-4GB RAM, TinyLlama)
	@echo "$(GREEN)🪶 Starting MyCoder Ultra-Lightweight...$(RESET)"
	@echo "$(YELLOW)📊 Optimized: 2-4GB RAM, 1-2 CPU, 637MB model$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.lightweight.yml up --build

light-detached: ## 🌙 Lightweight na pozadí  
	@echo "$(GREEN)🪶 Starting Lightweight (detached)...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.lightweight.yml up --build -d
	@echo "$(CYAN)💡 Use 'make logs-light' to see output$(RESET)"

##@ 🔨 Build & Maintenance

build-dev: ## 🔨 Rebuild development image
	@echo "$(GREEN)🔨 Building development image...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml build --no-cache

build-prod: ## 🔨 Rebuild production image
	@echo "$(GREEN)🔨 Building production image...$(RESET)"
	$(DOCKER_COMPOSE) build --no-cache

rebuild: ## 🔄 Rebuild všechny images
	@echo "$(GREEN)🔄 Rebuilding all images...$(RESET)"
	@$(MAKE) build-dev
	@$(MAKE) build-prod

clean: ## 🧹 Vyčisti Docker cache a stopped kontejnery
	@echo "$(RED)🧹 Cleaning Docker resources...$(RESET)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

deep-clean: ## 🧹💥 Kompletní cleanup včetně images
	@echo "$(RED)🧹💥 Deep cleaning Docker resources...$(RESET)"
	@echo "$(YELLOW)⚠️  This will remove ALL unused Docker resources!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -af --volumes; \
		echo "$(GREEN)✅ Deep cleanup complete$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled$(RESET)"; \
	fi

##@ 🔍 Testing & Debugging

test: ## 🧪 Spustí testy v development prostředí
	@echo "$(GREEN)🧪 Running tests...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -m pytest tests/ -v

test-local: ## 🧪 Spustí testy lokálně (PYTHON)
	@echo "$(GREEN)🧪 Running local tests...$(RESET)"
	$(PYTHON) -m pytest tests/ -v

test-integration: ## 🧪 Spustí integration testy
	@echo "$(GREEN)🧪 Running integration tests...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python quick_deepseek_test.py

test-quick: ## ⚡ Rychlé testy (jen základní)
	@echo "$(GREEN)⚡ Quick tests...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -c "\
		import sys; sys.path.insert(0, '/app/src'); \
		from mycoder.ollama_integration import OllamaClient; \
		import asyncio; \
		asyncio.run(OllamaClient().is_available()) and print('✅ OK') or print('❌ FAIL')"

lint: ## 📋 Code linting
	@echo "$(GREEN)📋 Running linting...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -m flake8 src/ tests/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -m black --check src/ tests/

lint-local: ## 📋 Lint lokálně (PYTHON)
	@echo "$(GREEN)📋 Running local linting...$(RESET)"
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m black --check src/ tests/

format: ## 🎨 Format kódu
	@echo "$(GREEN)🎨 Formatting code...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -m black src/ tests/

format-local: ## 🎨 Formátuj lokálně (PYTHON)
	@echo "$(GREEN)🎨 Formatting local code...$(RESET)"
	$(PYTHON) -m black src/ tests/

venv: ## 🐍 Vytvoří lokální venv a nainstaluje závislosti (Poetry)
	@echo "$(GREEN)🐍 Creating local venv...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install poetry
	POETRY_VIRTUALENVS_CREATE=false $(VENV_BIN)/poetry install --no-interaction --no-root

##@ 📊 Monitoring & Logs

logs: ## 📋 Zobraz logy development serveru
	@echo "$(GREEN)📋 Showing development logs...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f mycoder-dev

logs-prod: ## 📋 Zobraz logy production serveru
	@echo "$(GREEN)📋 Showing production logs...$(RESET)"
	$(DOCKER_COMPOSE) logs -f mycoder

logs-light: ## 🪶 Zobraz logy lightweight serveru
	@echo "$(GREEN)🪶 Showing lightweight logs...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.lightweight.yml logs -f mycoder-light

logs-ollama: ## 🤖 Zobraz logy Ollama
	@echo "$(GREEN)🤖 Showing Ollama logs...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f mycoder-dev | grep -i ollama

status: ## 📊 Stav všech služeb
	@echo "$(GREEN)📊 MyCoder Services Status:$(RESET)"
	@echo ""
	@echo "$(CYAN)Development:$(RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml ps 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "$(CYAN)Production:$(RESET)"  
	@$(DOCKER_COMPOSE) ps 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "$(CYAN)Docker Images:$(RESET)"
	@docker images | grep mycoder || echo "  No MyCoder images found"

health: ## 💓 Health check všech služeb
	@echo "$(GREEN)💓 Health Check...$(RESET)"
	@echo "Ollama API:"
	@curl -s http://localhost:11434/api/tags >/dev/null && echo "  ✅ OK" || echo "  ❌ DOWN"
	@echo "MyCoder API:"  
	@curl -s http://localhost:8000/health >/dev/null && echo "  ✅ OK" || echo "  ❌ DOWN (or no health endpoint)"

##@ 🎮 Control

stop: ## 🛑 Zastaví všechny služby
	@echo "$(RED)🛑 Stopping all services...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) down 2>/dev/null || true

restart: ## 🔄 Restart development serveru
	@echo "$(GREEN)🔄 Restarting development server...$(RESET)"
	@$(MAKE) stop
	@$(MAKE) dev-detached

restart-prod: ## 🔄 Restart production serveru
	@echo "$(GREEN)🔄 Restarting production server...$(RESET)"
	$(DOCKER_COMPOSE) restart

##@ 📚 Rychlé příkazy

quick-start: ## ⚡ Rychlý start pro nové uživatele
	@echo "$(CYAN)⚡ MyCoder Quick Start$(RESET)"
	@echo "$(YELLOW)===================$(RESET)"
	@echo "1. Starting development environment..."
	@$(MAKE) dev-detached
	@sleep 5
	@echo "2. Running health check..."
	@$(MAKE) health
	@echo "3. Running quick test..."
	@$(MAKE) test-quick
	@echo ""
	@echo "$(GREEN)🎉 MyCoder is ready!$(RESET)"
	@echo "$(CYAN)💡 Useful commands:$(RESET)"
	@echo "  make dev-shell  - Open development shell"
	@echo "  make logs       - View logs"  
	@echo "  make test       - Run tests"
	@echo "  make stop       - Stop all services"

demo: ## 🎬 Demo MyCoder funkcionality
	@echo "$(GREEN)🎬 MyCoder Demo...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec -T mycoder-dev python -c "\
		import sys; sys.path.insert(0, '/app/src'); \
		print('🎯 MyCoder Demo'); \
		print('Testing DeepSeek integration...'); \
		import asyncio; \
		from mycoder.ollama_integration import OllamaClient, CodeGenerationProvider; \
		async def demo(): \
			async with OllamaClient() as client: \
				if await client.is_available(): \
					provider = CodeGenerationProvider(client); \
					if await provider.is_ready(): \
						result = await provider.generate_code('Create hello world function', language='python'); \
						print('Generated code:'); \
						print(result.get('content', 'No content')[:200] + '...'); \
					else: \
						print('Provider not ready'); \
				else: \
					print('Ollama not available'); \
		asyncio.run(demo())"

##@ 📖 Info

info: ## ℹ️ Informace o MyCoder setup
	@echo "$(CYAN)ℹ️  MyCoder Setup Information$(RESET)"
	@echo "$(YELLOW)==========================$(RESET)"
	@echo "Development files:"
	@echo "  📁 docker-compose.dev.yml - Development environment"
	@echo "  📁 Dockerfile.dev         - Development image"  
	@echo "  📁 docker-entrypoint.dev.sh - Development entrypoint"
	@echo ""
	@echo "Production files:"
	@echo "  📁 docker-compose.yml     - Production environment"
	@echo "  📁 Dockerfile             - Production image"
	@echo "  📁 docker-entrypoint.sh   - Production entrypoint"
	@echo ""
	@echo "Current model: $(YELLOW)DeepSeek Coder 1.3B$(RESET)"
	@echo "Live reload: $(GREEN)✅ Enabled in development$(RESET)"
	@echo ""

ports: ## 🔌 Zobraz používané porty
	@echo "$(CYAN)🔌 MyCoder Ports$(RESET)"
	@echo "$(YELLOW)===============$(RESET)"
	@echo "Development:"
	@echo "  🌐 8000  - MyCoder API"
	@echo "  🤖 11434 - Ollama API"  
	@echo "  🐛 5678  - Python Debugger"
	@echo ""
	@echo "Production:"
	@echo "  🌐 8000  - MyCoder API"
	@echo "  🤖 11434 - Ollama API"
	@echo ""

##@ 🔧 Advanced

dev-rebuild-quick: ## ⚡ Rychlý rebuild dev (jen kód, ne modely)
	@echo "$(GREEN)⚡ Quick development rebuild...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml build mycoder-dev
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d mycoder-dev

dev-logs-tail: ## 📋 Tail posledních 100 řádků logů
	@echo "$(GREEN)📋 Last 100 log lines...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs --tail=100 mycoder-dev

dev-models: ## 🤖 Zobraz dostupné modely v dev prostředí
	@echo "$(GREEN)🤖 Available models in development:$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec mycoder-dev ollama list

pull-models: ## 📥 Stáhni nejnovější modely
	@echo "$(GREEN)📥 Pulling latest models...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec mycoder-dev ollama pull deepseek-coder:1.3b-base-q4_0
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec mycoder-dev ollama pull deepseek-coder:6.7b-instruct-q4_0

##@ ❓ Help

examples: ## 💡 Příklady použití
	@echo "$(CYAN)💡 MyCoder Usage Examples$(RESET)"
	@echo "$(YELLOW)========================$(RESET)"
	@echo ""
	@echo "$(GREEN)Development workflow:$(RESET)"
	@echo "  make dev                 # Start development server"
	@echo "  # Edit files in src/     # Changes are live-reloaded!"
	@echo "  make logs                # Watch logs in real-time"
	@echo "  make dev-shell           # Debug in container"
	@echo "  make test                # Run tests"
	@echo "  make stop                # Stop when done"
	@echo ""
	@echo "$(GREEN)Production deployment:$(RESET)"  
	@echo "  make prod                # Start production server"
	@echo "  make logs-prod           # Monitor production logs"
	@echo ""
	@echo "$(GREEN)Maintenance:$(RESET)"
	@echo "  make rebuild             # Rebuild after dependency changes"
	@echo "  make clean               # Clean up Docker resources"
	@echo "  make health              # Check service health"
	@echo ""

troubleshoot: ## 🔧 Troubleshooting guide
	@echo "$(CYAN)🔧 MyCoder Troubleshooting$(RESET)"
	@echo "$(YELLOW)===========================$(RESET)"
	@echo ""
	@echo "$(RED)Problem:$(RESET) Live reload nefunguje"
	@echo "$(GREEN)Solution:$(RESET) Zkontroluj že máš správně mounted volumes:"
	@echo "  $(DOCKER_COMPOSE) -f docker-compose.dev.yml config | grep -A5 volumes"
	@echo ""
	@echo "$(RED)Problem:$(RESET) Ollama se nespustí"  
	@echo "$(GREEN)Solution:$(RESET) Zkontroluj porty a restartuj:"
	@echo "  make stop && make dev"
	@echo ""
	@echo "$(RED)Problem:$(RESET) Pomalé buildy"
	@echo "$(GREEN)Solution:$(RESET) Použij development mode:"
	@echo "  make dev  # Místo make prod"
	@echo ""
	@echo "$(RED)Problem:$(RESET) Models se nestahují"
	@echo "$(GREEN)Solution:$(RESET) Manuální stažení:"
	@echo "  make pull-models"
	@echo ""
