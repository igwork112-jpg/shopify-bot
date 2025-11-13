#!/bin/bash

echo "========================================"
echo "Starting Shopify Review Bot on Railway"
echo "========================================"

# Ensure directories exist
mkdir -p logs temp

# Check if Playwright browsers are installed
echo "Checking Playwright installation..."
if [ ! -d "/ms-playwright/chromium-1097" ]; then
    echo "Installing Playwright browsers..."
    playwright install chromium
    playwright install-deps chromium || true
fi

echo "Playwright ready!"
echo "========================================"

# Start the application
python app.py
