#!/bin/bash

# Railway deployment script
echo "🚀 Starting YouTube AI Assistant deployment..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables
export HOST=0.0.0.0
export PORT=${PORT:-8000}
export DEBUG=False

# Start the server
echo "🌟 Starting server on port $PORT..."
cd server
python start_production.py