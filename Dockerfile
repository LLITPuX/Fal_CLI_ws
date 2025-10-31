FROM python:3.12-slim

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

WORKDIR /app

# Python deps for FastAPI app
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy entrypoint
USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown app:app /entrypoint.sh
USER app

EXPOSE 8000

# Entrypoint will stage credentials before running the CMD from compose
ENTRYPOINT ["/entrypoint.sh"]

