# YouTube AI Assistant - Launch Script
# PowerShell script to start the YouTube AI Assistant server

Write-Host "🎥 YouTube AI Assistant Server" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\myenv\Scripts\Activate.ps1"

# Navigate to server directory
Set-Location "server"

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host ""
    Write-Host "⚠️  Please edit server/.env and add your API keys:" -ForegroundColor Red
    Write-Host "   - GEMINI_API_KEY (for advanced Q&A with Google Gemini)" -ForegroundColor White
    Write-Host "   - YOUTUBE_API_KEY (for video metadata)" -ForegroundColor White
    Write-Host ""
}

# Start the server
Write-Host "Starting server on http://127.0.0.1:8000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

try {
    # Set Python path and start server
    $env:PYTHONPATH = "."
    python -c "
import sys
import os
sys.path.insert(0, '.')
from app.main import app
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)
"
}
catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
    Write-Host "Make sure all dependencies are installed:" -ForegroundColor Yellow
    Write-Host "pip install fastapi uvicorn python-dotenv youtube-transcript-api requests pydantic" -ForegroundColor White
}