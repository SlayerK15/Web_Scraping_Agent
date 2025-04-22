#!/bin/bash
set -e

# Create necessary directories
mkdir -p /app/storage/data
mkdir -p /app/storage/selectors
mkdir -p /app/storage/feedback
mkdir -p /app/logs

# Function to check if variable is set
is_set() {
    if [ -z "${!1}" ]; then
        return 1  # Variable is not set
    else
        return 0  # Variable is set
    fi
}

# Check required API keys
if is_set ANTHROPIC_API_KEY; then
    echo "Using Anthropic API"
elif is_set OPENAI_API_KEY; then
    echo "Using OpenAI API"
else
    echo "Warning: No AI API key found. Either ANTHROPIC_API_KEY or OPENAI_API_KEY must be set."
fi

# Setup Proxy Service if specified
PROXY_SERVICE=$(grep -oP '"service":\s*"\K[^"]+' /app/config/settings.json 2>/dev/null || echo "none")
if [ "$PROXY_SERVICE" = "brightdata" ] && ! is_set BRIGHTDATA_API_KEY; then
    echo "Warning: BrightData proxy service selected but BRIGHTDATA_API_KEY not set"
fi
if [ "$PROXY_SERVICE" = "scraperapi" ] && ! is_set SCRAPERAPI_API_KEY; then
    echo "Warning: ScraperAPI proxy service selected but SCRAPERAPI_API_KEY not set"
fi
if [ "$PROXY_SERVICE" = "zyte" ] && ! is_set ZYTE_API_KEY; then
    echo "Warning: Zyte proxy service selected but ZYTE_API_KEY not set"
fi

# Add the parent directory to Python path
export PYTHONPATH=$PYTHONPATH:/app

# Run the passed command
exec "$@"