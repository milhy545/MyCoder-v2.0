# 🤖 MyCoder - Dockerfile with Ollama integration
FROM python:3.14-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create app directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/
COPY README.md LICENSE ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Create mycoder user
RUN useradd -m -u 1000 mycoder && chown -R mycoder:mycoder /app
USER mycoder

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Start script
COPY docker-entrypoint.sh /app/
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER mycoder

CMD ["/app/docker-entrypoint.sh"]
