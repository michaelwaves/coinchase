# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm installation
RUN node --version && npm --version

# Install Claude Code globally and verify
RUN npm install -g @anthropic-ai/claude-code \
    && npm list -g @anthropic-ai/claude-code \
    && echo "Claude Code installed successfully"

# Find and add npm global bin to PATH
RUN npm_global_prefix=$(npm root -g) && \
    npm_global_bin=$(dirname $npm_global_prefix)/bin && \
    echo "NPM Global bin: $npm_global_bin" && \
    ls -la $npm_global_bin || echo "Bin directory not found"

# Add npm global bin directories to PATH
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models routers services utils prompts

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV NODE_PATH=/usr/local/lib/node_modules

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

