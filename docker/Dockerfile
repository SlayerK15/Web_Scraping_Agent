FROM python:3.9-slim

LABEL maintainer="Web Scraper AI Team"
LABEL description="AI-powered web scraper with automatic selector generation"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    dnsutils \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/storage/data /app/storage/selectors /app/storage/feedback /app/logs

# Set proper permissions
RUN chmod +x /app/docker/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Default command
CMD ["python", "-m", "main"]