FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates unzip bash git nodejs npm \
 && rm -rf /var/lib/apt/lists/*

# Install npm-based Gemini CLI as root (global)
RUN npm install -g @google/gemini-cli --omit=dev

# Create non-root user
RUN useradd -ms /bin/bash app
USER app
WORKDIR /home/app

# Directory for CLI auth (mounted at runtime)
RUN mkdir -p /home/app/.gemini

# Set up Python environment
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R app:app /app/data

# Copy application code
COPY --chown=app:app app /app/app

# Copy entrypoint script
USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown app:app /entrypoint.sh
USER app

EXPOSE 8000

# Entrypoint will stage credentials before running the CMD from compose
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]

