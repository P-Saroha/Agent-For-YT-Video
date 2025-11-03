# 🚀 Universal AI Assistant - Quick Start Script
# Run this file to start your server automatically!

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      🚀 Starting Universal AI Assistant Server...      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

# Check if in correct directory
$currentDir = Get-Location
if ($currentDir.Path -notlike "*video-ai-assistant*") {
    Write-Host "⚠️  Warning: You might not be in the project directory" -ForegroundColor Yellow
    Write-Host "   Current: $currentDir" -ForegroundColor Gray
    Write-Host "   Expected: F:\YT\video-ai-assistant" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Exiting..." -ForegroundColor Red
        exit
    }
}

Write-Host "📂 Project Directory: $currentDir" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Step 1/3: Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\myenv\Scripts\Activate.ps1") {
    & ".\myenv\Scripts\Activate.ps1"
    Write-Host "   ✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "   ❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Please run: python -m venv myenv" -ForegroundColor Yellow
    exit
}

Write-Host ""

# Navigate to server directory
Write-Host "Step 2/3: Navigating to server directory..." -ForegroundColor Yellow
if (Test-Path ".\server") {
    Set-Location ".\server"
    Write-Host "   ✅ Changed to server directory" -ForegroundColor Green
} else {
    Write-Host "   ❌ Server directory not found!" -ForegroundColor Red
    exit
}

Write-Host ""

# Check if API key is set
Write-Host "Step 3/3: Checking configuration..." -ForegroundColor Yellow
if (Test-Path "..\\.env") {
    Write-Host "   ✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "   Creating from .env.example..." -ForegroundColor Gray
    if (Test-Path "..\\.env.example") {
        Copy-Item "..\\.env.example" "..\\.env"
        Write-Host "   ✅ Created .env file" -ForegroundColor Green
        Write-Host "   ⚠️  Please update GEMINI_API_KEY in .env file!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Start the server
Write-Host "🚀 Starting FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "📱 Server will be available at:" -ForegroundColor Cyan
Write-Host "   • Main App:    http://localhost:8000 ⭐ (opens automatically)" -ForegroundColor White
Write-Host "   • Alt URL:     http://localhost:8000/app" -ForegroundColor White
Write-Host "   • API Info:    http://localhost:8000/api" -ForegroundColor White
Write-Host "   • API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Start the server
python start_server.py
